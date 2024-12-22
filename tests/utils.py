from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from fastapi_admin_next.db_connect import Base


class RelatedModel(Base):
    __tablename__ = "related_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    related_models = relationship("MockModel", back_populates="related")

    def __str__(self) -> str:
        return "RelatedModel"


class MockModel(Base):
    __tablename__ = "mock_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    enum_field = Column(Enum("option1", "option2", name="test_enum"))  # type: ignore
    related_id = Column(Integer, ForeignKey("related_model.id"))
    related = relationship("RelatedModel", back_populates="related_models")
