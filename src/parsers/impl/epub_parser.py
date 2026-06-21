from parsers.bookParserProvider import BookParser
from pathlib import Path
from sympy import content
from ebooklib import epub, ITEM_IMAGE,ITEM_DOCUMENT
from bs4 import BeautifulSoup

output_dir = Path("imgs")
output_dir.mkdir(exist_ok=True)

class EpubParser(BookParser):

    def extract_text(self, file_path: Path) -> str:
        book = epub.read_epub(file_path)
        image_map = self.extract_images(file_path)
        
        for item_id, _ in book.spine:

            item = book.get_item_with_id(item_id)

            if item is None:
                continue


            print("\nARQUIVO:", item.file_name)


            soup = BeautifulSoup(
                item.get_content(),
                "html.parser"
            )


            for element in soup.find_all(
                ["h1", "h2", "p", "img", "a"]
            ):

                if element.name == "img":

                    filename = Path(
                        element.get("src", "")
                    ).name

                    print({
                        "type": "img",
                        "src": image_map.get(filename)
                    })


                elif element.name == "a":

                    print({
                        "type": "a",
                        "text": element.get_text(
                            " ",
                            strip=True
                        ),
                        "href": element.get("href")
                    })


                else:

                    text = element.get_text(
                        " ",
                        strip=True
                    )

                    if text:

                        print({
                            "type": element.name,
                            "text": text[:50]
                        })
        return ""

    def extract_images(self,file_path:Path) -> dict:
        book = epub.read_epub(file_path)
        image_map = {}
    
        for img in book.get_items_of_type(ITEM_IMAGE):
            local_path = output_dir / Path(img.file_name).name

        with open(local_path, "wb") as f:
            f.write(img.get_content())

        image_map[Path(img.file_name).name] = str(local_path)

        return image_map