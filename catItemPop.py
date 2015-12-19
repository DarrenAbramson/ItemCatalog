from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Item, User, Base

engine = create_engine('sqlite:///catalogdatabase.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Create dummy user
User2 = User(name="Rick", email="rick@rickandmorty.com",
             picture='http://i.imgur.com/w0lX5kV.png')
session.add(User2)
session.commit()

# Create dummy user
User3 = User(name="Morty", email="rick@rickandmorty.com",
             picture='http://i.imgur.com/MS4ntmY.png')
session.add(User3)
session.commit()


#### Add categories ####

# Rap Category
cat1 = Category(name="Rap")

session.add(cat1)
session.commit()

# Electrohouse Category
cat2 = Category(name="Electrohouse")

session.add(cat2)
session.commit()

# Grunge Category
cat3 = Category(name="Grunge")

session.add(cat3)
session.commit()


#### Add Items ####

item1 = Item(user_id=2, name="The Beastie Boys", description=
             "Which song from 'Hello Nasty' was never performed live?",
                     category_name="Rap")
session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Tyler the Creator", description=
             "Juicy grilled rhymes with a side of irony",
             category_name="Rap")
session.add(item2)
session.commit()

item3 = Item(user_id=2, name="Run D.M.C.", description=
             "The Jason Nevins remix of 'It's Like That' must be witnessed.",
             category_name="Rap")
session.add(item3)
session.commit()

item4 = Item(user_id=3, name="Deadmau5", description=
             "What happens when the mouse head comes off!?",
             category_name="Electrohouse")
session.add(item4)
session.commit()

item5 = Item(user_id=3, name="Vitalic", description=
             "The video for 'Fade Away' is so confusing.",
             category_name="Electrohouse")
session.add(item5)
session.commit()

item6 = Item(user_id=2, name="Pearl Jam", description=
             "The most overrated band of the '90s.",
             category_name="Grunge")
session.add(item6)
session.commit()

item7 = Item(user_id=1, name="Nirvana", description=
             """Reinforces the popular notion of the tortured genius. And
              the 27 club.""",
             category_name="Grunge")
session.add(item7)
session.commit()



print "added some cats and items!"
