from pydantic import BaseModel, Field, ConfigDict, model_validator


class ConceptNode(BaseModel):
    """Schema for an individual concept node."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    description: str = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_concept_integrity(self):
        if self.id in self.prerequisites:
            raise ValueError(
                f"Concept '{self.id}' cannot be its own prerequisite."
            )
        if self.id in self.related_concepts:
            raise ValueError(
                f"Concept '{self.id}' cannot be related to itself."
            )
        if len(self.prerequisites) != len(set(self.prerequisites)):
            raise ValueError(
                f"Duplicate prerequisites found in '{self.id}'."
            )
        if len(self.related_concepts) != len(set(self.related_concepts)):
            raise ValueError(
                f"Duplicate related concepts found in '{self.id}'."
            )
        return self


class PrerequisiteGraphData(BaseModel):
    """Complete subject-specific concept graph configuration."""

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    concepts: list[ConceptNode]

    @model_validator(mode="after")
    def validate_concept_references(self):
        concept_ids = [concept.id for concept in self.concepts]
        if len(concept_ids) != len(set(concept_ids)):
            raise ValueError("Duplicate concept IDs found in graph.")

        known_ids = set(concept_ids)
        for concept in self.concepts:
            for prerequisite in concept.prerequisites:
                if prerequisite not in known_ids:
                    raise ValueError(
                        f"Unknown prerequisite '{prerequisite}' "
                        f"referenced by '{concept.id}'."
                    )
            for related in concept.related_concepts:
                if related not in known_ids:
                    raise ValueError(
                        f"Unknown related concept '{related}' "
                        f"referenced by '{concept.id}'."
                    )
        return self
