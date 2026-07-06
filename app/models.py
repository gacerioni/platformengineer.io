from dataclasses import dataclass, field, asdict
from typing import Dict, List


@dataclass
class Demo:
    slug: str
    title: str
    tagline: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    links: Dict[str, str] = field(default_factory=dict)
    status: str = ""
    icon: str = "box"
    featured: bool = False
    protected: bool = False
    order: int = 0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class Post:
    slug: str
    title: str
    summary: str = ""
    body_md: str = ""
    tags: List[str] = field(default_factory=list)
    published_at: str = ""
    reading_minutes: int = 5
    draft: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class Event:
    slug: str
    title: str
    date: str = ""
    location: str = ""
    link: str = ""
    kind: str = "talk"

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)
