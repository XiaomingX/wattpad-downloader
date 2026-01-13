import os
import re
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
import chainlit as cl
from core import (
    retrieve_story,
    slugify,
    wp_get_cookies,
    fetch_story_from_partId,
    logger,
    CachedSession,
    cache,
    headers,
    get_metadata_text,
    download_chapter,
    fetch_cover,
)

DOWNLOAD_ROOT = Path("downloads")

def get_book_dir(story_title: str, story_id: str) -> Path:
    dir_name = f"{slugify(story_title)}_{story_id}"
    path = DOWNLOAD_ROOT / dir_name
    path.mkdir(parents=True, exist_ok=True)
    return path

def sanitize_filename(filename: str) -> str:
    # Basic filename sanitization
    return re.sub(r'[\\/*?:\"<>|]', "", filename).strip()

@cl.on_chat_start
async def start():
    content = (
        "Welcome to **Wattpad Downloader (TXT Mode)**! 📚\n\n"
        "Please enter a Wattpad **Story URL**, **Chapter URL**, or **Story ID**.\n\n"
        "Chapters will be saved as individual `.txt` files in a folder named after the book."
    )
    await cl.Message(content=content).send()

@cl.on_message
async def main(message: cl.Message):
    input_text = message.content.strip()
    
    # Robust URL parsing using regex
    # Story: wattpad.com/story/123456789
    # Part: wattpad.com/123456789
    story_match = re.search(r"wattpad\.com/story/(\d+)", input_text)
    part_match = re.search(r"wattpad\.com/(\d+)", input_text)
    
    download_id = None
    mode = "story"
    
    if story_match:
        download_id = story_match.group(1)
        mode = "story"
    elif part_match:
        download_id = part_match.group(1)
        mode = "part"
    elif input_text.isdigit():
        download_id = input_text
        mode = "story"

    if not download_id:
        await cl.Message(content="❌ **Invalid Wattpad URL or ID.**").send()
        return

    try:
        cookies = None # Could add login logic if needed later
        
        async with CachedSession(
            headers=headers, 
            cookies=cookies, 
            cache=cache, 
            trust_env=True
        ) as session:
            logger.info(f"Fetching metadata for {mode} {download_id}")
            async with cl.Step(name="Fetching Metadata") as step:
                if mode == "story":
                    metadata = await retrieve_story(int(download_id), cookies, session=session)
                else:
                    story_id_str, metadata = await fetch_story_from_partId(int(download_id), cookies, session=session)
                    download_id = story_id_str
                step.output = f"Fetched metadata for: {metadata['title']}"
                logger.info(f"Metadata fetched: {metadata['title']}")

            # Create book directory
            book_dir = get_book_dir(metadata['title'], download_id)
            
            # Save Metadata
            async with cl.Step(name="Saving Metadata") as step:
                metadata_path = book_dir / "metadata.txt"
                metadata_content = get_metadata_text(metadata)
                await cl.make_async(metadata_path.write_text)(metadata_content, encoding="utf-8")
                
                # Save Cover if available
                cover_path = book_dir / "cover.jpg"
                try:
                    cover_data = await fetch_cover(metadata['cover'], session=session)
                    await cl.make_async(cover_path.write_bytes)(cover_data)
                except Exception as e:
                    logger.warning(f"Failed to download cover: {e}")
                
                step.output = f"Metadata and cover saved to {book_dir}"

            # Progress tracking
            total_chapters = len(metadata["parts"])
            logger.info(f"Starting download of {total_chapters} chapters")
            
            async with cl.Step(name="Downloading Chapters") as step:
                for idx, part in enumerate(metadata["parts"]):
                    current_idx = idx + 1
                    chapter_title = part['title']
                    
                    # Download and clean
                    chapter_content = await download_chapter(part, cookies=cookies, session=session)
                    
                    # Save to file
                    safe_title = sanitize_filename(chapter_title)
                    file_name = f"{current_idx:03d}_{safe_title}.txt"
                    file_path = book_dir / file_name
                    
                    await cl.make_async(file_path.write_text)(chapter_content, encoding="utf-8")
                    
                    progress_msg = f"Saved chapter {current_idx}/{total_chapters}: {chapter_title}"
                    step.output = progress_msg
                    logger.info(progress_msg)

        await cl.Message(
            content=f"✅ Successfully downloaded: **{metadata['title']}**\n\nAll chapters saved in: `{book_dir}`"
        ).send()

    except Exception as e:
        logger.exception("Download failed")
        await cl.Message(content=f"An error occurred: {str(e)}").send()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)