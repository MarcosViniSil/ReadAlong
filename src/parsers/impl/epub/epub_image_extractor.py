from pathlib import Path
from ebooklib import ITEM_IMAGE
from log.loggerService import LoggerService

output_dir = Path("imgs")
output_dir.mkdir(exist_ok=True)

class ImageExtractor:
    @staticmethod
    def extract_images(book):
        image_map = {}
        image_items = list(book.get_items_of_type(ITEM_IMAGE))
        LoggerService.log_info("Found %d image(s) in EPUB", len(image_items))

        for img in image_items:
            file_name = Path(img.file_name).name
            local_path = output_dir / file_name

            try:
                with open(local_path, "wb") as f:
                    f.write(img.get_content())
                image_map[file_name] = str(local_path)
                LoggerService.log_debug("Extracted image '%s' to '%s'", file_name, local_path)
            except OSError as e:
                LoggerService.log_error("Failed to write image '%s' to '%s': %s", file_name, local_path, e)

        LoggerService.log_info("Image extraction complete: %d image(s) saved to disk", len(image_map))
        return image_map