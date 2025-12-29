from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from .config import OPENAI_API_KEY

class SyllabusOutput(BaseModel):
    topics: List[str] = Field(description="List of syllabus topics/modules")

def generate_syllabus_ai(course_name: str, course_desc: str, competencies: list[dict]) -> list[str]:
    """
    Generates a course program (syllabus) using LangChain and OpenAI.
    """
    
    if not OPENAI_API_KEY:
        print("[AI SERVICE] OPENAI_API_KEY not set. Returning fallback.")
        return []

    try:
        # Initialize the model
        model = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            temperature=0.7
        )

        # parser
        parser = JsonOutputParser(pydantic_object=SyllabusOutput)

        # Format competencies text
        comp_text = "\n".join([f"- {c.get('name')}" for c in competencies])

        # Define template
        template = """
        Você é um especialista pedagógico do SENAC.
        Analise o seguinte curso e suas competências associadas:

        CURSO: {course_name}
        DESCRIÇÃO: {course_desc}

        COMPETÊNCIAS ESPERADAS:
        {comp_text}

        TAREFA:
        Crie uma estrutura de conteúdo programático (Syllabus) logica e sequencial para este curso.
        O programa deve ter entre 4 e 8 tópicos principais.
        Os tópicos devem ser curtos, diretos e profissionais. 
        Não numere os tópicos na string (ex: "1. Introdução" -> "Introdução").
        
        {format_instructions}
        """

        prompt = PromptTemplate(
            template=template,
            input_variables=["course_name", "course_desc", "comp_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        # Create chain
        chain = prompt | model | parser

        # Invoke chain
        result = chain.invoke({
            "course_name": course_name,
            "course_desc": course_desc,
            "comp_text": comp_text
        })

        # Extract topics
        return result.get("topics", [])

    except Exception as e:
        print(f"[AI SERVICE] Error generating syllabus: {str(e)}")
        return []
