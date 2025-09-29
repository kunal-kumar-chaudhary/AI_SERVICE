from neo4j import GraphDatabase
import os

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"), auth=("kkunal644@gmail.com", os.getenv("NEO4J_PASSWORD"))
)


def ensure_neo4j_constraints():
    """
    ensure a uniqueness contraint on Entity.name 
    """
    try:
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE"
            )
    except Exception as e:
        print(f"Error creating constraints: {e}")
    