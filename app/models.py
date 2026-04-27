from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Course(Base):
    __tablename__ = "courses"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow)

    sections = relationship(
        "Section",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Section.order",
    )


class Section(Base):
    __tablename__ = "sections"

    id         = Column(Integer, primary_key=True, index=True)
    course_id  = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title      = Column(String(255), nullable=False)
    order      = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    course  = relationship("Course", back_populates="sections")
    classes = relationship(
        "Class",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Class.order",
    )


class Class(Base):
    __tablename__ = "classes"

    id            = Column(Integer, primary_key=True, index=True)
    section_id    = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title         = Column(String(255), nullable=False)
    order         = Column(Integer, default=0)
    raw_narration = Column(Text, default="")
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="classes")
