"""Script to visualize Pydantic models using Mermaid and Graphviz."""
from pydantic_mermaid import MermaidGenerator # type: ignore
from typing import List, Dict, Any 
import graphviz # type: ignore 

from src.config import (
    TABLE_BORDER,
    CELL_BORDER,
    CELL_SPACING,
    CELL_PADDING,
    BG_COLOR,
    HEADER_COLOR,
    REF_KEY,
)


class Visualizer:
    def __init__(self, models_to_visualize: List):
        self.generator = MermaidGenerator(models_to_visualize)
        
    def generate_mermaid_schema(self) -> str:
        """
        Generates the Mermaid class diagram code for the Pydantic models.
        """
        mermaid_text = self.generator.generate_chart() 
        return mermaid_text

    def generate_detailed_graph(self, schema_dict: Dict[str, Any]): 
        """
        Generates a detailed Graphviz relationship diagram from a JSON Schema,
        using HTML labels to display fields and data types within the nodes.
        """
        dot = graphviz.Digraph(
            comment='Pydantic Schema Relationship',
            graph_attr={'rankdir': 'LR', 'splines': 'ortho'}
        )
        
        for name, definition in schema_dict.get('definitions', {}).items():

            label_html = f'<<TABLE BORDER="{TABLE_BORDER}" CELLBORDER="{CELL_BORDER}" CELLSPACING="{CELL_SPACING}" CELLPADDING="{CELL_PADDING}" BGCOLOR="{BG_COLOR}">'

            label_html += f'<TR><TD COLSPAN="2" BGCOLOR="{HEADER_COLOR}"><B>{name}</B></TD></TR>'

            properties = definition.get('properties', {})
            for prop_name, prop_data in properties.items():

                prop_type = prop_data.get('type', 'N/A')
                prop_data.get('description', '')

                if REF_KEY in prop_data:
                    ref_name = prop_data[REF_KEY].split('/')[-1]
                    port_id = prop_name
                    label_html += f'<TR><TD PORT="{port_id}" ALIGN="LEFT">{prop_name}</TD><TD ALIGN="LEFT">List[{ref_name}]</TD></TR>'
                else:
                    label_html += f'<TR><TD ALIGN="LEFT">{prop_name}</TD><TD ALIGN="LEFT">{prop_type.capitalize()}</TD></TR>'

            label_html += '</TABLE>>'

            dot.node(name, label=label_html, shape='none')

        for name, definition in schema_dict.get('definitions', {}).items():
            for prop_name, prop_data in definition.get('properties', {}).items():
                if REF_KEY in prop_data: 
                    ref_name = prop_data[REF_KEY].split('/')[-1]
                
                    dot.edge(f'{name}:{prop_name}', ref_name, label='')


        dot.render('detailed_pydantic_schema', view=True, format='png')
        print("--- Graphviz Output ---")
        print("Detailed graph saved as detailed_pydantic_schema.png and attempting to open.")