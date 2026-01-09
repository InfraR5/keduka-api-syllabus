from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from typing import List
from pydantic import BaseModel, Field
from .config import ORCHESTRATOR_URL
from .schemas import AgentOutput
from .core.llm_adapter import OrchestratorChatModel
import json

class SyllabusOutput(BaseModel):
    topics: List[str] = Field(description="List of syllabus topics/modules")

def generate_syllabus_ai(course_name: str, course_desc: str, competencies: list[dict], system_prompt: str = None, temperature: float = 0.7, top_p: float = None, frequency_penalty: float = None, presence_penalty: float = None) -> list[str]:
    """
    Generates a course program (syllabus) using LangChain with Orchestrator Adapter.
    """
    
    # Pass params via constructor
    model = OrchestratorChatModel(
        orchestrator_url=ORCHESTRATOR_URL,
        origin_service="md-api-secao",
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    
    parser = JsonOutputParser(pydantic_object=SyllabusOutput)

    # Format competencies text to string
    comp_text = "\n".join([f"- {c.get('name')}" for c in competencies])

    # If system_prompt is provided, we use it to override the default "System" instructions
    # OR we set it as a SystemMessage.
    
    default_template = """
    Você é um especialista pedagógico do SENAC.
    Analise o seguinte curso e suas competências associadas:

    CURSO: {course_name}
    DESCRIÇÃO: {course_desc}

    COMPETÊNCIAS ESPERADAS:
    {comp_text}

    TAREFA:
    Crie uma estrutura de conteúdo programático (Syllabus) lógica e sequencial para este curso.
    O programa deve ter entre 4 e 8 tópicos principais.
    Os tópicos devem ser curtos, diretos e profissionais. 
    Não numere os tópicos na string.
    
    {format_instructions}
    """
    
    from langchain_core.messages import SystemMessage, HumanMessage

    if system_prompt:
        # If user provides system prompt, we use strictly that as SystemMessage
        # And keep the task data in UserMessage
        # But we need to ensure {format_instructions} is handled.
        
        # Strategy: Use the user provided system prompt as the "Persona/System"
        # and keep the task structure.
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"CURSO: {course_name}\nDESCRIÇÃO: {course_desc}\nCOMPETÊNCIAS: {comp_text}\n\n{parser.get_format_instructions()}")
        ]
        
        chain = model | parser
        
        try:
            result = chain.invoke(messages)
            return result.get("topics", [])
        except Exception as e:
            print(f"[AI SERVICE] Error generating syllabus (custom prompt): {str(e)}")
            return []

    else:
        # Default legacy flow with PromptTemplate
        prompt = PromptTemplate(
            template=default_template,
            input_variables=["course_name", "course_desc", "comp_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | model | parser

        try:
            result = chain.invoke({
                "course_name": course_name,
                "course_desc": course_desc,
                "comp_text": comp_text
            })
            return result.get("topics", [])
        except Exception as e:
            print(f"[AI SERVICE] Error generating syllabus: {str(e)}")
            return []

def generate_full_structure(objetivo: str, publico: str, nivel: str) -> AgentOutput:
    """
    Generates the full competency and course structure using LangChain via Orchestrator.
    """
    
    model = OrchestratorChatModel(
        orchestrator_url=ORCHESTRATOR_URL,
        origin_service="md-api-secao"
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

    print(f"[AI AGENT] Generating structure via Orchestrator for: {objetivo}")
    
    try:
        result = chain.invoke({
            "objetivo": objetivo,
            "publico": publico,
            "nivel": nivel
        })
        
        return AgentOutput(**result)

    except Exception as e:
        print(f"[AI AGENT] Error: {str(e)}")
        raise e
