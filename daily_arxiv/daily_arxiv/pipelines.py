# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import arxiv
from scrapy.exceptions import DropItem

class DailyArxivPipeline:
    def __init__(self):
        self.page_size = 100
        self.client = arxiv.Client(self.page_size)

    def _matches_keywords(self, item: dict) -> bool:
        keywords = [
            k.strip().lower()
            for k in os.environ.get("KEYWORDS", "").split(",")
            if k.strip()
        ]

        if not keywords:
            return True

        text = " ".join([
            item.get("title") or "",
            item.get("summary") or "",
            item.get("comment") or "",
            " ".join(item.get("categories") or []),
        ]).lower()

        return any(keyword in text for keyword in keywords)

    def process_item(self, item: dict, spider):
        item["pdf"] = f"https://arxiv.org/pdf/{item['id']}"
        item["abs"] = f"https://arxiv.org/abs/{item['id']}"

        search = arxiv.Search(id_list=[item["id"]])
        paper = next(self.client.results(search))

        item["authors"] = [a.name for a in paper.authors]
        item["title"] = paper.title
        item["categories"] = paper.categories
        item["comment"] = paper.comment
        item["summary"] = paper.summary

        if not self._matches_keywords(item):
            raise DropItem(f"Not in configured interests: {item['id']}")

        return item
