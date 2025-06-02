import sys
import calendar
import logging
import datetime
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Any
from tqdm import tqdm

log = logging.getLogger(__name__)


def safe_parse_date(
    year: str, month: str, day: str, pmid: Optional[str] = None, context: str = ""
) -> Optional[str]:
    """
    Safely parse a date from string or integer values, correcting invalid days where possible.

    Args:
        year (str): Year component of the date.
        month (str): Month component of the date.
        day (str): Day component of the date.
        pmid (str): PubMed ID for context logging.
        context (str): Context for which the date is being parsed.

    Returns:
        Optional[str]: ISO formatted date string if successful; otherwise, None.
    """
    try:
        return datetime.date(int(year), int(month), int(day)).isoformat()
    except ValueError as e:
        log.warning(
            f"[PMID: {pmid}] Invalid date ({year}-{month}-{day}) in {context}. Attempting correction..."
        )
        try:
            # Try to fix common issues like invalid day in month
            last_day = calendar.monthrange(int(year), int(month))[1]
            corrected_day = min(int(day), last_day)
            corrected_date = datetime.date(
                int(year), int(month), corrected_day
            ).isoformat()
            log.info(f"[PMID: {pmid}] Corrected date to: {corrected_date}")
            return corrected_date
        except Exception as ex:
            log.error(f"[PMID: {pmid}] Date correction failed: {ex}")
            return None


class ArticleTransformer:
    def __init__(self, element_tree: ET.Element):
        """
        Initialize the ArticleTransformer.

        Args:
            element_tree (ET.Element): XML tree representing a PubMed article.
        """
        self.tree: ET.Element = element_tree
        self.pmid = None
        self.title = None
        self.vernacular_title = None
        self.abstract = None
        self.other_abstract = None
        self.language = None
        self.status = None
        self.article_date = None
        self.history = []
        self.authors = []
        self.grants = []
        self.chemicals = []
        self.keywords = []
        self.mesh_terms = []
        self.publication_types = []
        self.journal_information = None
        self.full_text_url = "NA"
        self.vectorised_flag = "N"
        self.nlp_processed_flag = "N"
        self.full_text = "NA"

        self._parse_article()

    def _parse_article(self) -> None:
        """
        Extracts all required fields from the XML tree.
        """
        # Basic identifiers and metadata
        pmid_elem = self.tree.find(".//PMID")
        if pmid_elem is not None:
            self.pmid = pmid_elem.text

        # ArticleTitle
        x_title = self.tree.find(".//ArticleTitle")
        if x_title is not None:
            self.title = "".join(list(x_title.itertext()))

        # Vernacular Title
        x_vernacular_title = self.tree.find(".//VernacularTitle")
        if x_vernacular_title is not None:
            self.vernacular_title = "".join(list(x_vernacular_title.itertext()))

        # other abstract equivalent to abstract
        x_other_abstr = self.tree.find(".//OtherAbstract")
        if x_other_abstr is not None:
            self.other_abstract = []
            all_other_text = x_other_abstr.findall(".//AbstractText")

            for t in all_other_text:
                self.other_abstract.append("".join(list(t.itertext())))

            self.other_abstract = " ".join(self.other_abstract)

        # Abstract, the loop is used to separate new sections with a blank space at the beginning
        x_abstr = self.tree.find(".//Abstract")
        if x_abstr is not None:
            self.abstract = []
            all_text = x_abstr.findall(".//AbstractText")

            for t in all_text:
                self.abstract.append("".join(list(t.itertext())))

            self.abstract = " ".join(self.abstract)

        # language
        x_language = self.tree.find(".//Language")
        if x_language is not None:
            self.language = x_language.text

        # status
        self.status = self.tree.find(".//MedlineCitation").attrib["Status"]

        # history
        x_history = self.tree.find(".//History")
        if x_history is not None:
            self.history = []
            for child in x_history:
                c_year = child.find(".//Year").text
                c_month = child.find(".//Month").text
                c_day = child.find(".//Day").text

                c_date = safe_parse_date(
                    c_year, c_month, c_day, pmid=self.pmid, context="History"
                )

                self.history.append(
                    {
                        "Date": c_date,
                        "Type": child.attrib["PubStatus"],
                    }
                )

        # Date
        x_article_date = self.tree.find(".//ArticleDate")
        if x_article_date is not None:
            year = x_article_date.find(".//Year").text
            month = x_article_date.find(".//Month").text
            day = x_article_date.find(".//Day").text

            self.article_date = safe_parse_date(
                year, month, day, pmid=self.pmid, context="ArticleDate"
            )
        else:
            x_pubdate = self.tree.find(".//PubDate")
            if x_pubdate is not None and len(x_pubdate.findall("child")) == 3:
                if x_pubdate.find(".//Month").text.isalpha():
                    month = list(calendar.month_abbr).index(
                        x_pubdate.find(".//Month").text
                    )
                else:
                    month = x_pubdate.find(".//Month").text

                year = x_pubdate.find(".//Year").text
                day = x_pubdate.find(".//Day").text

                self.article_date = safe_parse_date(
                    year, month, day, pmid=self.pmid, context="ArticleDate"
                )

        if self.article_date is None:
            for h in self.history:
                if h["Type"] == "entrez":
                    self.article_date = h["Date"]

        if self.article_date is None:
            self.article_date = self.history[0]["Date"]

        # authors
        x_authors_list = self.tree.find(".//AuthorList")

        if x_authors_list is not None:
            self.authors = []
            x_authors = x_authors_list.findall(".//Author")

            for xauth in x_authors:
                forename, lastname, affi = None, None, None

                x_forename = xauth.find(".//ForeName")
                if x_forename is not None:
                    forename = x_forename.text

                x_lastname = xauth.find(".//LastName")
                if x_lastname is not None:
                    lastname = x_lastname.text

                x_affi = xauth.findall(".//Affiliation")

                if x_affi is not None:
                    affi = []
                    if x_affi is not None:
                        [affi.append({"Institute": a.text}) for a in x_affi]

                self.authors.append(
                    {"ForeName": forename, "LastName": lastname, "Affiliations": affi}
                )

        # grants
        x_grants_list = self.tree.find(".//GrantList")
        x_grants = []

        if x_grants_list is not None:
            self.grants = []
            x_grants = x_grants_list.findall(".//Grant")

            for x_grant in x_grants:
                grant_id, acronym, agency, country = None, None, None, None

                x_grant_id = x_grant.find(".//GrantID")
                if x_grant_id is not None:
                    grant_id = x_grant_id.text

                x_acronym = x_grant.find(".//Acronym")
                if x_acronym is not None:
                    acronym = x_acronym.text

                x_agency = x_grant.find(".//Agency")
                if x_agency is not None:
                    agency = x_agency.text

                x_country = x_grant.find(".//Country")
                if x_country is not None:
                    country = x_country.text

                self.grants.append(
                    {
                        "ResearchGrantID": grant_id,
                        "Acronym": acronym,
                        "Agency": agency,
                        "Country": country,
                    }
                )

        # chemicals
        x_chemicals_list = self.tree.find(".//ChemicalList")
        x_chemicals = []

        if x_chemicals_list is not None:
            self.chemicals = []
            x_chemicals = x_chemicals_list.findall(".//Chemical")

            for x_chemical in x_chemicals:
                registry_number, name_of_sub, chemical_ui = None, None, None

                x_registry_number = x_chemical.find(".//RegistryNumber")
                if x_registry_number is not None:
                    registry_number = x_registry_number.text

                x_name_of_sub = x_chemical.find(".//NameOfSubstance")
                if x_name_of_sub is not None:
                    chemical_ui = x_name_of_sub.attrib["UI"]
                    name_of_sub = x_name_of_sub.text

                self.chemicals.append(
                    {
                        "MeshUI": chemical_ui,
                        "Name": name_of_sub,
                    }
                )

        # keywords
        x_key_list = self.tree.find(".//KeywordList")
        x_keywords = []

        if x_key_list is not None:
            self.keywords = []
            x_keywords = x_key_list.findall(".//Keyword")

        for x_key in x_keywords:
            self.keywords.append(
                {"Name": x_key.text, "Major": x_key.attrib["MajorTopicYN"] == "Y"}
            )
        # meshterms
        x_mesh_list = self.tree.find(".//MeshHeadingList")
        x_mesh_headers = []

        if x_mesh_list is not None:
            self.mesh_terms = []
            x_mesh_headers = x_mesh_list.findall(".//MeshHeading")

            for x_mesh in x_mesh_headers:

                (
                    descr,
                    descr_ui,
                    descr_ismajor,
                    qual,
                    qual_ui,
                    qual_ismajor,
                ) = (
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )

                x_desc = x_mesh.find(".//DescriptorName")
                if x_desc is not None:
                    descr = x_desc.text
                    descr_ui = x_desc.attrib["UI"]
                    descr_ismajor = x_desc.attrib["MajorTopicYN"] == "Y"

                xqual = x_mesh.find(".//QualifierName")
                if xqual is not None:
                    qual = xqual.text
                    qual_ui = xqual.attrib["UI"]
                    qual_ismajor = x_desc.attrib["MajorTopicYN"] == "Y"

                self.mesh_terms.append(
                    {"MeshUI": descr_ui, "Name": descr, "Major": descr_ismajor}
                )

        # publicationType
        x_publication_type_list = self.tree.find(".//PublicationTypeList")
        x_pub_types = []

        if x_publication_type_list is not None:
            self.publication_types = []
            x_pub_types = x_publication_type_list.findall(".//PublicationType")

            for x_type in x_pub_types:
                self.publication_types.append(
                    {
                        "MeshUI": x_type.attrib["UI"],
                        "Name": x_type.text,
                    }
                )

        # journal Information
        x_journal_information = self.tree.find(".//Journal")

        if x_journal_information is not None:
            self.journal_information = None

            journal_title, journal_abbreviation = None, None
            journal_issue_information = None

            x_journal_title = x_journal_information.find(".//Title")
            if x_journal_title is not None:
                journal_title = x_journal_title.text

            x_journal_abbreviation = x_journal_information.find(".//ISOAbbreviation")
            if x_journal_abbreviation is not None:
                journal_abbreviation = x_journal_abbreviation.text

            journal_issue, journal_volume, journal_issue_number, journal_issue_year = (
                None,
                None,
                None,
                None,
            )

            x_journal_issue_type = x_journal_information.find(".//JournalIssue")
            if x_journal_issue_type is not None:
                journal_issue = x_journal_issue_type.attrib["CitedMedium"]

                if x_journal_issue_type.find("Volume") is not None:
                    journal_volume = x_journal_issue_type.find("Volume").text

                if x_journal_issue_type.find("Issue") is not None:
                    journal_issue_number = x_journal_issue_type.find("Issue").text

                if x_journal_issue_type.find("PubDate") is not None:
                    journal_issue_year, journal_issue_month, journal_issue_day = (
                        None,
                        None,
                        None,
                    )

                    if x_journal_issue_type.find("PubDate").find("Year") is not None:
                        journal_issue_year = (
                            x_journal_issue_type.find("PubDate").find("Year").text
                        )

                    if x_journal_issue_type.find("PubDate").find("Month") is not None:
                        if (
                            x_journal_issue_type.find("PubDate")
                            .find("Month")
                            .text.isalpha()
                        ):
                            journal_issue_month = list(calendar.month_abbr).index(
                                x_journal_issue_type.find("PubDate").find("Month").text
                            )
                        else:
                            journal_issue_month = (
                                x_journal_issue_type.find("PubDate").find("Month").text
                            )

                    if x_journal_issue_type.find("PubDate").find("Day") is not None:
                        journal_issue_day = (
                            x_journal_issue_type.find("PubDate").find("Day").text
                        )

                    journal_issue_date = {
                        "year": journal_issue_year,
                        "month": journal_issue_month,
                        "day": journal_issue_day,
                    }

                journal_issue_information = {
                    "JournalIssueMedium": journal_issue,
                    "JournalVolume": journal_volume,
                    "JournalIssueNumber": journal_issue_number,
                    "JournalIssueDate": journal_issue_date,
                }

            self.journal_information = {
                "JournalTitle": journal_title,
                "Abbreviation": journal_abbreviation,
                "JournalIssue": journal_issue_information,
            }

    def get_data_dict(self) -> Dict[str, Any]:
        """
        Convert the parsed article into a dictionary.

        Returns:
            Dict[str, Any]: Structured data representation of the article.
        """
        return {
            "PMID": self.pmid,
            "Title": self.title,
            "VernacularTitle": self.vernacular_title,
            "Abstract": self.abstract,
            "OtherAbstract": self.other_abstract,
            "Language": self.language,
            "Status": self.status,
            "ArticleDate": self.article_date,
            "History": self.history,
            "Authors": self.authors,
            "Grants": self.grants,
            "Chemicals": self.chemicals,
            "Keywords": self.keywords,
            "MeshTerms": self.mesh_terms,
            "PublicationTypes": self.publication_types,
            "JournalInformation": self.journal_information,
            "FullTextURL": self.full_text_url,
            "VectorisedFlag": self.vectorised_flag,
            "NLPProcessedFlag": self.nlp_processed_flag,
            "FullText": self.full_text,
        }


# Only PubMedArticle are extracted not the PubmedBookArticle
def transform_articles(xml_article_set: str) -> List[Dict[str, Any]]:
    """
    Transform a set of PubMed articles in XML format into structured dictionaries.

    Args:
        xml_article_set (str): XML string of PubMedArticleSet.

    Returns:
        List[Dict[str, Any]]: List of structured article representations.
    """
    transformed_articles = []
    set_tree = ET.fromstring(xml_article_set)

    for element in tqdm(set_tree, desc="Processing the records present: "):
        if element.tag == "PubmedArticle":
            try:
                article = ArticleTransformer(element)
                transformed_articles.append(article.get_data_dict())
            except Exception as e:
                err_pmid = element.find(".//PMID").text
                error_message = (
                    f"Transformation was unsuccessful for PMID: {err_pmid} \n{e}"
                )
                log.error(error_message)  # Log to file
                print(error_message)  # Display to command line
                input(
                    "Press Enter to acknowledge the error and terminate the script..."
                )
                sys.exit(1)  # Exit the script with a non-zero exit code

        else:
            log.info(f"Document {element} is having tag: {element.tag}")

    return transformed_articles
