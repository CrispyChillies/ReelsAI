'''
Ref: https://www.marktechpost.com/2025/05/15/a-step-by-step-guide-to-build-an-automated-knowledge-graph-pipeline-using-langgraph-and-networkx/
'''

import networkx as nx
import matplotlib.pyplot as plt
from typing import TypedDict, List, Tuple, Dict, Any
from django.conf import settings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .system_prompts import ENTITY_EXTRACTOR_PROMPT, RELATION_EXTRACTOR_PROMPT, ENTITY_RESOLVER_PROMPT

# Entity types for extraction
ENTITY_TYPES = ["Person", "Organization", "Location", "Product", "Concept", "Event", "Other"]

class KGState(TypedDict):
    topic: str
    raw_text: str
    entities: List[Dict[str, str]]  # List of {name: str, type: str}
    relations: List[Tuple[str, str, str]]  # (subject, relation, object)
    resolved_relations: List[Tuple[str, str, str]]
    graph: Any
    validation: Dict[str, Any]
    messages: List[Any]
    current_agent: str
    llm: Any  # LLM instance to be passed through the pipeline

def data_gatherer(state: KGState) -> KGState:
    """
    Data gatherer now receives raw text to process.
    In a real implementation, this could fetch data from various sources.
    """
    print(f"📥 Data Gatherer: Processing text about '{state['topic']}'")
    
    # The raw_text should already be provided in the initial state
    if not state["raw_text"]:
        raise ValueError("No raw text provided to process")
    
    state["messages"].append(AIMessage(content=f"Processing text about {state['topic']} ({len(state['raw_text'])} characters)"))
    state["current_agent"] = "entity_extractor"
    
    return state


def entity_extractor(state: KGState) -> KGState:
    """
    Uses LLM to extract entities from text and classify them by type.
    """
    print("🔍 Entity Extractor: Identifying entities using LLM")
    
    llm = state["llm"]
    text = state["raw_text"]
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=ENTITY_EXTRACTOR_PROMPT),
        HumanMessage(content=f"Text to analyze:\n\n{text}\n\nExtract entities and their types from this text.")
    ])
    
    # Set up JSON output parser
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        # Invoke the LLM
        response = chain.invoke({})
        entities = response.get("entities", [])
        
        # Add the main topic as a Concept if not already present
        entity_names = [e["name"].lower() for e in entities]
        if state["topic"].lower() not in entity_names:
            entities.insert(0, {"name": state["topic"], "type": "Concept"})
        
        state["entities"] = entities
        state["messages"].append(AIMessage(content=f"Extracted {len(entities)} entities using LLM"))
        # print(f"   ✓ Found {len(entities)} entities: {[e['name'] for e in entities[:5]]}{'...' if len(entities) > 5 else ''}")
        print(f"   ✓ Found {len(entities)} entities: {[e['name'] for e in entities]}")
        
    except Exception as e:
        print(f"   ⚠ Error in entity extraction: {e}")
        # Fallback to empty list
        state["entities"] = [{"name": state["topic"], "type": "Concept"}]
        state["messages"].append(AIMessage(content=f"Entity extraction failed, using fallback: {e}"))
    
    state["current_agent"] = "relation_extractor"
    return state


def relation_extractor(state: KGState) -> KGState:
    """
    Uses LLM to extract relationships between identified entities.
    """
    print("🔗 Relation Extractor: Identifying relationships using LLM")
    
    llm = state["llm"]
    text = state["raw_text"]
    entities = state["entities"]
    entity_names = [e["name"] for e in entities]
    
    # Create the prompt
    entities_str = "\n".join([f"- {e['name']} ({e['type']})" for e in entities])
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=RELATION_EXTRACTOR_PROMPT),
        HumanMessage(content=f"""Text to analyze:
            {text}

            Entities identified:
            {entities_str}

            Extract relationships between these entities from the text.""")
    ])
    
    # Set up JSON output parser
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        # Invoke the LLM
        response = chain.invoke({})
        relations_list = response.get("relations", [])
        
        # Convert to tuples and validate
        relations = []
        for rel in relations_list:
            if len(rel) == 3:
                subject, relation, obj = rel
                # Verify entities exist in our entity list (case-insensitive)
                entity_names_lower = [e.lower() for e in entity_names]
                if subject.lower() in entity_names_lower and obj.lower() in entity_names_lower:
                    relations.append((subject, relation, obj))
        
        state["relations"] = relations
        state["messages"].append(AIMessage(content=f"Extracted {len(relations)} relationships using LLM"))
        print(f"   ✓ Found {len(relations)} relationships:")
        print(f"{[rel for rel in relations]}")
        
    except Exception as e:
        print(f"   ⚠ Error in relation extraction: {e}")
        state["relations"] = []
        state["messages"].append(AIMessage(content=f"Relation extraction failed: {e}"))
    
    state["current_agent"] = "entity_resolver"
    return state


def entity_resolver(state: KGState) -> KGState:
    """
    Uses LLM to resolve duplicate or similar entities.
    """
    print("🔄 Entity Resolver: Resolving duplicate entities using LLM")
    
    llm = state["llm"]
    entities = state["entities"]
    
    # Create entities list for the prompt
    entities_str = "\n".join([f"- {e['name']} (Type: {e['type']})" for e in entities])
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=ENTITY_RESOLVER_PROMPT),
        HumanMessage(content=f"""Entities to resolve:
        {entities_str}

        Identify groups of entities that should be merged together.""")
    ])
    
    # Set up JSON output parser
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    try:
        # Invoke the LLM
        response = chain.invoke({})
        resolutions = response.get("resolutions", [])
        
        # Build entity mapping
        entity_map = {}
        for resolution in resolutions:
            canonical = resolution["canonical"]
            aliases = resolution.get("aliases", [])
            for alias in aliases:
                entity_map[alias.lower()] = canonical
        
        # Map all entities to their canonical forms
        for entity in entities:
            entity_name = entity["name"]
            if entity_name.lower() not in entity_map:
                entity_map[entity_name.lower()] = entity_name
        
        # Apply resolution to relations
        resolved_relations = []
        for s, p, o in state["relations"]:
            s_resolved = entity_map.get(s.lower(), s)
            o_resolved = entity_map.get(o.lower(), o)
            resolved_relations.append((s_resolved, p, o_resolved))
        
        # Remove duplicate relations
        resolved_relations = list(set(resolved_relations))
        
        state["resolved_relations"] = resolved_relations
        state["messages"].append(AIMessage(content=f"Resolved entities and updated {len(resolved_relations)} relationships"))
        print(f"   ✓ Applied {len(resolutions)} entity resolutions")
        print(f"{[res for res in resolutions]}")
        
    except Exception as e:
        print(f"   ⚠ Error in entity resolution: {e}")
        # Fallback: use relations as-is
        state["resolved_relations"] = state["relations"]
        state["messages"].append(AIMessage(content=f"Entity resolution failed, using original relations: {e}"))
    
    state["current_agent"] = "graph_integrator"
    return state

def graph_integrator(state: KGState) -> KGState:
    """
    Builds the knowledge graph from resolved relations.
    """
    print("🌐 Graph Integrator: Building the knowledge graph")
    G = nx.DiGraph()
   
    for s, p, o in state["resolved_relations"]:
        if not G.has_node(s):
            G.add_node(s)
        if not G.has_node(o):
            G.add_node(o)
        G.add_edge(s, o, relation=p)
   
    state["graph"] = G
    state["messages"].append(AIMessage(content=f"Built graph with {len(G.nodes)} nodes and {len(G.edges)} edges"))
    print(f"   ✓ Graph built: {len(G.nodes)} nodes, {len(G.edges)} edges")
   
    state["current_agent"] = "graph_validator"
   
    return state


def graph_validator(state: KGState) -> KGState:
    """
    Validates the constructed knowledge graph.
    """
    print("✅ Graph Validator: Validating knowledge graph")
    G = state["graph"]
   
    validation_report = {
        "num_nodes": len(G.nodes),
        "num_edges": len(G.edges),
        "is_connected": nx.is_weakly_connected(G) if len(G.nodes) > 0 else False,
        "has_cycles": not nx.is_directed_acyclic_graph(G) if len(G.nodes) > 0 else False,
        "density": nx.density(G) if len(G.nodes) > 0 else 0,
        "isolated_nodes": list(nx.isolates(G)) if len(G.nodes) > 0 else []
    }
   
    state["validation"] = validation_report
    state["messages"].append(AIMessage(content=f"Validation report: {validation_report}"))
    print(f"   ✓ Validation complete:")
    print(f"      - Nodes: {validation_report['num_nodes']}")
    print(f"      - Edges: {validation_report['num_edges']}")
    print(f"      - Connected: {validation_report['is_connected']}")
    print(f"      - Has cycles: {validation_report['has_cycles']}")
    print(f"      - Isolated nodes: {len(validation_report['isolated_nodes'])}")
   
    state["current_agent"] = END
   
    return state


def router(state: KGState) -> str:
    """
    Routes to the next agent in the pipeline.
    """
    return state["current_agent"]


def visualize_graph(graph, title="Knowledge Graph"):
    """
    Visualizes the knowledge graph using matplotlib.
    """
    if len(graph.nodes) == 0:
        print("⚠ Cannot visualize empty graph")
        return
    
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(graph, k=0.5, iterations=50)
   
    # Draw nodes with different colors based on centrality
    node_sizes = [300 + 700 * nx.degree_centrality(graph).get(node, 0) for node in graph.nodes()]
    nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=node_sizes, alpha=0.9)
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, edge_color='gray', arrows=True, 
                           arrowsize=20, arrowstyle='->', alpha=0.6)
    
    # Draw labels
    nx.draw_networkx_labels(graph, pos, font_size=9, font_weight='bold')
   
    # Draw edge labels (relations)
    edge_labels = nx.get_edge_attributes(graph, 'relation')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=7)
   
    plt.title(title, fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.show()


def build_kg_graph():
    """
    Builds and compiles the LangGraph workflow for knowledge graph construction.
    """
    workflow = StateGraph(KGState)
   
    # Add nodes for each agent
    workflow.add_node("data_gatherer", data_gatherer)
    workflow.add_node("entity_extractor", entity_extractor)
    workflow.add_node("relation_extractor", relation_extractor)
    workflow.add_node("entity_resolver", entity_resolver)
    workflow.add_node("graph_integrator", graph_integrator)
    workflow.add_node("graph_validator", graph_validator)
   
    # Add conditional edges based on router
    workflow.add_conditional_edges("data_gatherer", router,
                                {"entity_extractor": "entity_extractor"})
    workflow.add_conditional_edges("entity_extractor", router,
                                {"relation_extractor": "relation_extractor"})
    workflow.add_conditional_edges("relation_extractor", router,
                                {"entity_resolver": "entity_resolver"})
    workflow.add_conditional_edges("entity_resolver", router,
                                {"graph_integrator": "graph_integrator"})
    workflow.add_conditional_edges("graph_integrator", router,
                                {"graph_validator": "graph_validator"})
    workflow.add_conditional_edges("graph_validator", router,
                                {END: END})
   
    workflow.set_entry_point("data_gatherer")
   
    return workflow.compile()


def run_knowledge_graph_pipeline(topic: str, raw_text: str, llm=None, model_name: str = "gpt-3.5-turbo", 
                                 temperature: float = 0.0):
    """
    Runs the complete knowledge graph construction pipeline.
    
    Args:
        topic: The main topic/subject of the knowledge graph
        raw_text: The text to extract knowledge from
        llm: Optional pre-configured LLM instance. If None, will create a ChatOpenAI instance
        model_name: The model to use if llm is not provided (default: gpt-3.5-turbo)
        temperature: Temperature for LLM generation (default: 0.0 for deterministic output)
    
    Returns:
        Final state containing the constructed knowledge graph
    """
    print(f"\n{'='*60}")
    print(f"🚀 Starting Knowledge Graph Pipeline")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    print(f"Text length: {len(raw_text)} characters")
    print(f"Model: {model_name if llm is None else 'Custom LLM'}")
    print(f"{'='*60}\n")
    
    # Initialize LLM if not provided
    if llm is None:
        llm = ChatOpenAI(model=model_name, temperature=temperature)
    
    initial_state = {
        "topic": topic,
        "raw_text": raw_text,
        "entities": [],
        "relations": [],
        "resolved_relations": [],
        "graph": None,
        "validation": {},
        "messages": [HumanMessage(content=f"Build a knowledge graph about {topic}")],
        "current_agent": "data_gatherer",
        "llm": llm
    }
   
    kg_app = build_kg_graph()
    final_state = kg_app.invoke(initial_state)
   
    print(f"\n{'='*60}")
    print(f"✅ Knowledge Graph Construction Complete")
    print(f"{'='*60}\n")
   
    return final_state

if __name__ == "__main__":
    # Example usage with a sample text
    topic = "Artificial Intelligence"
    
    sample_text = """
    Artificial Intelligence (AI) is transforming the world of technology. Companies like Google and OpenAI 
    are at the forefront of AI research. Google developed TensorFlow, a powerful machine learning framework, 
    while OpenAI created GPT models for natural language processing.
    
    Machine Learning is a subset of Artificial Intelligence that focuses on learning from data. Deep Learning, 
    in turn, is a specialized form of Machine Learning that uses neural networks. Neural networks are inspired 
    by the human brain and consist of interconnected nodes.
    
    Sam Altman is the CEO of OpenAI, leading the development of advanced AI systems. Sundar Pichai leads Google 
    and oversees their AI initiatives. Both organizations are based in the United States, with Google headquartered 
    in Mountain View, California.
    
    The field of AI has applications in various domains including healthcare, finance, and autonomous vehicles. 
    Self-driving cars, developed by companies like Tesla and Waynes, rely heavily on AI and computer vision 
    technologies.
    """

    try:
        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini",
            temperature=0.0
        )
        result = run_knowledge_graph_pipeline(
            topic=topic,
            raw_text=sample_text,
            model_name="gpt-4",  # or "gpt-4" for better results
            temperature=0.0,
            llm=llm
        )
        
        print("\n📊 Final Statistics:")
        print(f"   Entities: {len(result['entities'])}")
        print(f"   Relations: {len(result['relations'])}")
        print(f"   Resolved Relations: {len(result['resolved_relations'])}")
        print(f"   Graph Validation: {result['validation']}")
        
        # Visualize the graph
        visualize_graph(result["graph"], title=f"Knowledge Graph: {topic}")
        
    except Exception as e:
        print(f"\n❌ Error running pipeline: {e}")
        print("\nMake sure to:")
        print("1. Install required packages: pip install langchain langchain-openai langgraph networkx matplotlib")
        print("2. Set OPENAI_API_KEY environment variable")
        print("3. Or provide a custom LLM instance to run_knowledge_graph_pipeline()")
