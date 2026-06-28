from pathlib import Path
from ebooklib import ITEM_IMAGE

output_dir = Path("imgs")
output_dir.mkdir(exist_ok=True)

class ImageExtractor:
    @staticmethod
    def extract_images(self, book):
        image_map = {}

        for img in book.get_items_of_type(ITEM_IMAGE):

            local_path = output_dir / Path(img.file_name).name

            with open(local_path, "wb") as f:
                f.write(img.get_content())

            image_map[Path(img.file_name).name] = str(local_path)

        return image_map