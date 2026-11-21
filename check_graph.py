from backend.app.diagnosis.concept_graph import ConceptGraph

graph = ConceptGraph.load_from_json(
    "data/concepts/physics_force_motion.json"
)

print("\nMINDTRACE CONCEPT GRAPH")
print("-----------------------")
print(graph.get_graph_statistics())

print("\nLearning order for Newton's Second Law:")
print(
    graph.get_learning_order(
        ["newton_second_law"]
    )
)

print("\nMissing prerequisites for Kinetic Energy:")
print(
    graph.get_missing_prerequisites(
        "kinetic_energy",
        ["mass", "velocity"]
    )
)
