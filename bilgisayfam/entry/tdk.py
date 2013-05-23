# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests

from django.forms.models import model_to_dict

from entry.models import Entry, Meaning


def get_meaning(keyword):
    """
    Assuming that there are no Entry or Meaning objects in the DB for the
    given /keyword/, it makes a request and extracts data from TDK website
    and adds it to the DB.
    """
    form_fields = {"kelime": keyword}
    response = requests.post(
        "http://www.tdk.gov.tr/index.php?option=com_gts&arama=gts",
        data=form_fields)
    # TDK does not give 404 as response status but it does have specific
    # keywords which tell us the word could not be found.
    if u"sözü bulunamadı" in response.text:
        # Add an entry for this keyword.
        Entry.objects.create(keyword=keyword)
        return None
    soup = BeautifulSoup(response.text)
    table_tag = soup.select("#hor-minimalist-a")[0]
    meta_data_list = table_tag.select("thead i")[0].contents
    # keyword as returned from TDK web site.
    keyword = table_tag.select("thead > tr > th > b")[0].string.strip()

    entry_tags = list()
    extra_info = list()
    for meta_data_tag in meta_data_list:
        try:
            if meta_data_tag.name == "b":
                tag_list = unicode(meta_data_tag.string).split(',')
                entry_tags.extend(
                    map(lambda x: x.strip(), tag_list))
        except AttributeError:
            # Extra info like "ingilizce typhoon".
            tag_list = unicode(meta_data_tag.string).split(',')
            extra_info.extend(
                map(lambda x: x.strip(), tag_list))
    entry = Entry.objects.create(keyword=keyword, tags=entry_tags,
        extra_info=extra_info)
    entry_dict = model_to_dict(entry, fields=["tags", "extra_info",
                                              "keyword"])
    entry_dict["meaning"] = []
    for meaning_td in table_tag.select("td"):
        meaning_tags = list()
        content = unicode()
        for td_tag in meaning_td:
            try:
                if td_tag.name == 'i' and td_tag.string:
                    meaning_tags.extend(
                            unicode(td_tag.string).split(','))
            except AttributeError:
                content += unicode(td_tag.string)
        # Does not work when content is "2. 0,00156 gram olan" (zerre).
        content = content.strip().lstrip("0123456789. ")
        meaning = Meaning.objects.create(entry=entry, tags=meaning_tags,
            content=content.strip())
        meaning_dict = model_to_dict(meaning, fields=["tags", "content", ])
        entry_dict["meaning"].append(meaning_dict)
    return entry_dict
