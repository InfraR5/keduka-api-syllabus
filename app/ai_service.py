from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from .config import OPENAI_API_KEY
from .schemas import AgentOutput

class SyllabusOutput(BaseModel):
    topics: List[str] = Field(description="List of syllabus topics/modules")

def generate_syllabus_ai(course_name: str, course_desc: str, competencies: list[dict]) -> list[str]:
    """
    Generates a course program (syllabus) using LangChain and OpenAI.
    Reserved for the legacy/simple endpoint.
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

def generate_full_structure(objetivo: str, publico: str, nivel: str) -> AgentOutput:
    """
    Generates the full competency and course structure based on the Agent persona.
    """
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY not set")

    try:
        model = ChatOpenAI(
            model="gpt-4o", # Using 4o for higher reasoning quality as requested
            api_key=OPENAI_API_KEY,
            temperature=0.7
        )

        parser = JsonOutputParser(pydantic_object=AgentOutput)

        template = """
        Você é um agente de IA especialista em design instrucional, educação corporativa e integração com Moodle.
        Sua função é transformar uma intenção simples do usuário em uma estrutura educacional completa.

        O usuário informa:
        OBJETIVO: {objetivo}
        PÚBLICO: {publico}
        NÍVEL: {nivel}

        SUA TAREFA:
        1. Criar uma Competência com nome, nível, e uma descrição pedagógica rica (o que o aluno será capaz de fazer, contexto, raciocínio).
        2. Gerar um ID técnico para a competência (ex: COMP_DADOS_01).
        3. Definir a estrutura da competência (subcompetências).
        4. Criar Cursos necessários para atingir essa competência.
        5. Para cada curso, definir Carga Horária, Objetivo e Módulos.
        6. Para cada Módulo, definir Conteúdo, Atividade Prática e Avaliação.
        7. Definir Regras de Avaliação gerais.

        Siga estritamente o formato JSON solicitado.

        {format_instructions}
        """

        prompt = PromptTemplate(
            template=template,
            input_variables=["objetivo", "publico", "nivel"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | model | parser

        print(f"[AI AGENT] Generating structure for: {objetivo}")
        result = chain.invoke({
            "objetivo": objetivo,
            "publico": publico,
            "nivel": nivel
        })
        
        return AgentOutput(**result)

    except Exception as e:
        print(f"[AI AGENT] Error: {str(e)}")
        raise e
