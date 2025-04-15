import json
import requests
import LegalAI.settings as settings


def search(
    search_query, page_number=1, jurisdiction_id: str = None, jurisdiction_court_id=None
):
    if jurisdiction_court_id is not None:
        url = f"{settings.COURT_LISTENER_API_ADDRESS}search/?q={search_query}&page={page_number}&order_by=dateFiled+desc&court={jurisdiction_court_id}"
    elif jurisdiction_court_id is None and jurisdiction_id is not None:
        courts_list_by_jurisdiction = courts(jurisdiction_id)
        courts = ""
        for court_object in courts_list_by_jurisdiction:
            courts += f"{court_object['Id']} "
        url = f"{settings.COURT_LISTENER_API_ADDRESS}search/?q={search_query}&page={page_number}&order_by=dateFiled+desc&court={courts}"
    else:
        url = f"{settings.COURT_LISTENER_API_ADDRESS}search/?q={search_query}&page={page_number}&order_by=dateFiled+desc"
    payload = {}
    headers = {
        "Accept": "application/json",
        "Authorization": f"Token {settings.COURT_LISTENER_API_TOKEN}",
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    parsed_response = json.loads(response.text)
    search_results = []
    if parsed_response.get("results", None):
        results = parsed_response.get("results")
        for result in results:
            search_results.append(
                {
                    "id": result.get("id"),
                    "court_name": result.get("court"),
                    "case_name": result.get("caseName"),
                    "date_filed": result.get("dateFiled"),
                    "status": result.get("status"),
                    "citations": result.get("citation"),
                    "citations_count": result.get("citeCount"),
                    "docket_number": result.get("docketNumber"),
                    "docket_id": result.get("docket_id"),
                    "snippet": "..." + result.get("snippet") + "...",
                }
            )

    total_pages = parsed_response.get("count", 1)
    has_prev = False
    has_next = False
    if page_number != 1:
        has_prev = True
    if page_number < total_pages:
        has_next = True
    response = {
        "search_query": search_query,
        "search_results": parsed_response["results"],
        "pagination": {
            "page": page_number,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        },
        "success": True,
    }
    return response


def opinion(id):
    openion_url = f"{settings.COURT_LISTENER_API_ADDRESS}opinions/{id}/"

    payload = {}
    headers = {
        "Accept": "application/json",
        "Authorization": f"Token {settings.COURT_LISTENER_API_TOKEN}",
    }

    response = {
        "id": id,
        "case_name": None,
        "absolute_url": None,
        "date_filed": None,
        "status": None,
        "citations": None,
        "citations_count": None,
        "docket": None,
        "author": None,
        "court": None,
        "scdb_id": None,
        "content_detail": None,
        "content_summary": None,
        "authorities": [],
        "html_with_citaitions": None,
        "plain_text": None,
        "xml_harvard" : None
    }

    opinion_response = requests.request(
        "GET", openion_url, headers=headers, data=payload
    )
    opinion_response_parsed = json.loads(opinion_response.text)
    print(opinion_response_parsed)
    response["content_detail"] = opinion_response_parsed.get("html_lawbox")
    response["html_with_citaitions"] = opinion_response_parsed.get(
        "html_with_citations"
    )
    response["plain_text"] = opinion_response_parsed.get("plain_text")
    response["absolute_url"] = (
        settings.COURT_LISTENER_ADDRESS
        + opinion_response_parsed.get("absolute_url", "")
    )
    author_url = opinion_response_parsed["author"]
    if author_url:
        author_response = requests.request(
            "GET", author_url, headers=headers, data=payload
        )
        author_response_parsed = json.loads(author_response.text)
        response["author"] = {
            "id": author_response_parsed["id"],
            "first_name": author_response_parsed["name_first"],
            "middle_name": author_response_parsed["name_middle"],
            "last_name": author_response_parsed["name_last"],
            "gender": author_response_parsed["gender"],
        }

    cluster_url = opinion_response_parsed["cluster"]
    if cluster_url:
        cluster_response = requests.request(
            "GET", cluster_url, headers=headers, data=payload
        )
        cluster_response_parsed = json.loads(cluster_response.text)
        response["case_name"] = cluster_response_parsed.get("case_name", None)
        response["date_filed"] = cluster_response_parsed.get("date_filed", None)
        response["status"] = cluster_response_parsed.get("precedential_status", None)
        response["citations"] = cluster_response_parsed.get("citations", None)
        response["citations_count"] = cluster_response_parsed.get(
            "citation_count", None
        )
        response["scdb_id"] = cluster_response_parsed.get("scdb_id", None)
        response["content_summary"] = cluster_response_parsed.get("syllabus", None)

        docket_url = cluster_response_parsed["docket"]
        if docket_url:
            docket_response = requests.request(
                "GET", docket_url, headers=headers, data=payload
            )
            docket_response_parsed = json.loads(docket_response.text)
            response["docket"] = {
                "id": docket_response_parsed["id"],
                "number": docket_response_parsed["docket_number"],
            }
            court_url = docket_response_parsed["court"]
            if court_url:
                court_response = requests.request(
                    "GET", court_url, headers=headers, data=payload
                )
                court_response_parsed = json.loads(court_response.text)
                response["court"] = {
                    "full_name": court_response_parsed["full_name"],
                    "short_name": court_response_parsed["short_name"],
                    "url": court_response_parsed["url"],
                }

    return response


def courts(jurisdiction: str = None):
    courts_by_jurisdiction = []
    url = f"{settings.COURT_LISTENER_API_ADDRESS}courts/"
    params = {"jurisdiction": jurisdiction} if jurisdiction else {}
    headers = {
        "Accept": "application/json",
        "Authorization": f"Token {settings.COURT_LISTENER_API_TOKEN}",
    }

    has_next_page = True
    while has_next_page:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise exception for any HTTP error
        parsed_response = json.loads(response.text)
        courts_by_jurisdiction.extend(
            [
                {
                    "Id": court["id"],
                    "ShortName": court["short_name"],
                    "FullName": court["full_name"],
                }
                for court in parsed_response["results"]
            ]
        )
        has_next_page = parsed_response.get("next") is not None
        url = parsed_response.get("next")  # Update URL for next page if available

    return courts_by_jurisdiction
