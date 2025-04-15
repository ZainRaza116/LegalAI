import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
import LegalAI.settings as settings
from xhtml2pdf import pisa
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List


def GenerateRequestResponse(status, status_code, message, response):
    REQUEST_RESPONSE = {
        "status": status,
        "status_code": status_code,
        "message": message,
        "response": response,
    }
    return REQUEST_RESPONSE


def GetClientIpAddress(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def GetDocsFromVectorDB(
    embedding_model,
    query,
    extraLayer,
    db_path=os.path.join(
        settings.SYSTEM_VECTOR_DB_PATH, settings.VECTOR_DB_PERSIST_STORAGE
    ),
):
    results = None
    embedding = embedding_model
    if extraLayer:
        llm = OpenAI(model_name="gpt-4")
        res = llm(
            f"""
                I need you to convert "{query}" , a query from user in English Language if it is already not in English.
                I need you to convert it only if it has legal matter involved or references so that it easier to perform similarity search from vector Db of Legal Documents also include synonyms.
                If you think that the query is general e.g greetings and there is no need to perform similarity search from Vector DB of Court/Legal Documents, then return nothing.
                Only return search query, do not return any other text or explanation. Remember , return only text that will used in search, do not return useless explanation.
            """
        )
        if not len(res) > 5:
            return []
        vectordb = Chroma(persist_directory=db_path, embedding_function=embedding)
        results = vectordb.similarity_search_with_score(res)
    else:
        vectordb = Chroma(persist_directory=db_path, embedding_function=embedding)
        results = vectordb.similarity_search_with_score(query)

    return results


class GptTrigger:
    def __init__(self, _TriggerNumber, _TriggerContent) -> None:
        self.TriggerNumber = _TriggerNumber
        self.TriggerContent = _TriggerContent


def Handle_Files_Upload(file_array, directory, subdir):
    try:
        paths = []
        for file in file_array:
            filename = file.name
            path = os.path.join(directory, subdir, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            print(path)

            with open(path, "wb") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            paths.append(path)

        return paths
    except Exception as ex:
        print(ex)
        print("An Error occurred while uploading files:", str(ex))


def Render_HTML_Template(
    brief_template: settings.COURT_BRIEF_TEMPLATE_INFO,
    brief_info: settings.COURT_BRIEF_INFO,
):

    try:
        main_template_content = None
        question_template_content = None
        authority_template_content = None
        argument_template_content = None

        questions_content = ""
        authorities_content = ""
        arguments_content = ""

        with open(brief_template.MAIN_TEMPLATE, "r") as html_file:
            main_template_content = html_file.read()
        with open(brief_template.QUESTION_TEMPLATE, "r") as html_file:
            question_template_content = html_file.read()
        with open(brief_template.AUTHORITY_TEMPLATE, "r") as html_file:
            authority_template_content = html_file.read()
        with open(brief_template.ARGUMENT_TEMPLATE, "r") as html_file:
            argument_template_content = html_file.read()

        if len(brief_info.questions_presented) > 0:
            for question in brief_info.questions_presented:
                questions_content += question_template_content.replace(
                    "**##question##**", question
                )
        if len(brief_info.table_of_authorities) > 0:
            for authority in brief_info.table_of_authorities:
                authorities_content += authority_template_content.replace(
                    "**##authority##**", authority
                )
        if len(brief_info.arguments_of_case) > 0:
            for argument in brief_info.arguments_of_case:
                arguments_content += str(
                    argument_template_content.replace("**##title##**", argument.title)
                ).replace("**##description##**", argument.description)

        # Loop through each property in the JSON object
        for key in brief_info.__dict__.keys():
            value = getattr(brief_info, key)
            # Replace placeholder with corresponding value in HTML content
            placeholder = "**##" + key + "##**"
            html_file_content = main_template_content.replace(placeholder, str(value))

        return html_file_content

    except Exception as ex:
        print(ex)


def Convert_HTML_To_PDF(
    brief_template: settings.COURT_BRIEF_TEMPLATE_INFO,
    brief_info: settings.COURT_BRIEF_INFO,
    output_filename,
):
    # Ensure the directory for output exists, if not, create it
    output_directory = os.path.dirname(output_filename)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # open output file for writing (truncated binary)
    source_html = Render_HTML_Template(
        brief_template=brief_template, brief_info=brief_info
    )

    with open(output_filename, "w+b") as result_file:
        # convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            source_html, dest=result_file  # the HTML to convert
        )  # file handle to recieve result

    # return False on success and True on errors
    return pisa_status.err


class UserBriefArgumentStructure(BaseModel):
    title: str = Field(description="Title/Heading of the Argument of brief")
    description: str = Field(
        description="Description/Detailed discussion of the Argument of brief"
    )


class UserBriefStructure(BaseModel):
    court_name: str = Field(description="name of court in which brief will be filed")
    court_term: str = Field(description="term of court e.g Spring 2004")
    petitioner_name: str = Field(description="pettitioner name")
    respondent_name: str = Field(description="respondent name")
    title_of_brief: str = Field(description="title of brief")
    submitting_entity: str = Field(
        description="Name of persons/organizations submitting/filing the brief"
    )
    attorneys: List[str] = Field(
        description="list of strings/name of attorneys if any or name of person if he is representing himself"
    )
    questions_presented: List[str] = Field(
        description="list of questions presented in the brief, as many as possible but reasonable questions"
    )
    table_of_authorities: List[str] = Field(
        description="list names/titles of opinions/past cases used/reffered in brief"
    )
    statement_of_case: str = Field(
        description="statement of the case, as detailed as possible but still reasonable"
    )
    arguments_of_case: List["UserBriefArgumentStructure"] = Field(
        "list of arguments in the case ,atlease 3 but make as many as possible (be reasonable) "
    )
    summary_of_arguments: str = Field(description="summary of arguments in the brief")
    conclusion: str = Field(
        description="conclusion of the brief which must be solid, valid and accurate"
    )
