from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref
import datetime

# Main tool for using python to access SQL. Provided by sqlalchemy.
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    # URL, received via authentication with 3rd party?
    picture = Column(String(250))
    # Definitely received via 3rd party.
    # TODO: Hey for extra credit, how about an email registration option!?
    email = Column(String(250))

# NOTE: the specification asks for app_routes that have strings for items.

# This has the advantage of more readable URLs that don't include integer IDs.

# A disadvantage is that the primary key will no longer be a db-selectable
# nullable int.

# For these reasons, the Category and Item tables have a string as a
# non-nullable primary key.

# TODO: will have to do error checking for identical names.

# Category class.

# Categories are not tied to users, since permissions are tied to item creator.

# The specification does not explicitly say what order Categories
# should be reported in. It is clearly not alphabetical, so I'll add a date
# field and have it reported by newest.

# A backref relationship ensures that when Categories are listed for public APIs
# -- see XML and JSON routes -- that items will be appropriately nested in their
# category.


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    # dateAdded = Column(Date)
    items = relationship("Item", cascade="all, delete-orphan")
    @property
    def serialize(self):
        """Return object data in JSON form for promotion of web app."""
        """If the calling function wants to embed item information """
        """for each category it can do so."""
        return{
            'id':   self.id,
            'name': self.name,
            # 'date': self.dateAdded,
            'items': [i.serialize for i in self.items]
        }

# Item class.
# Items may only be deleted or edited by the person who created it.
# Each item falls under a single unique category.

class Item(Base):
    __tablename__ = 'item'
    category = relationship("Category", backref=backref("items", cascade=
														"all, delete-orphan"))
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    # The example Snowboard description is 406 characters. 2.5 times this
    # is sufficient to start.
    description = Column(String(1000))
    dateAdded = Column(DateTime, default=datetime.datetime.now,
                       onupdate=datetime.datetime.now)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    category_name = Column(String, ForeignKey('category.name'))
    category = relationship(Category)

    @property
    def serialize(self):
        """Return object data in JSON form for promotion of web app."""
        return {
            'id':           self.id,
            'name':         self.name,
            'description':  self.description,
            'owner':        self.user_id,
            'category':     self.category_name,
        }

engine = create_engine('sqlite:///catalogdatabase.db')

Base.metadata.create_all(engine)



