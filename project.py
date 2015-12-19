from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import dicttoxml
from xml.dom.minidom import parseString

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogdatabase.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# This route definition is taken verbatim from the Udacity OAUTH example.
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# This route definition is taken verbatim from the Udacity OAUTH example.
# Authenticate and store information on a Google login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s." % login_session['username'])
    print "done!"
    return output

# Disconnect based on provider
# Taken from Udacity example. Only Google implemented for now.
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatsAndItems'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatsAndItems'))

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
                                 json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
                                 json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Route for /
# Show all categories and items at the front page.
@app.route('/')
def showCatsAndItems():
    cats = session.query(Category)
    items = session.query(Item).order_by(desc(Item.dateAdded))
    if 'username' not in login_session:
        return render_template('publiccategories.html', cats = cats,
                               items = items)
    else:
        return render_template('categories.html', cats = cats,
                               items = items)

# Route for /catalog/<Category Name>/items
@app.route('/catalog/<string:category_name>/items')
def showCategory(category_name):
    cats = session.query(Category)
    items = session.query(Item).filter_by(
                category_name = category_name).all()
    if 'username' not in login_session:
        return render_template('publiccategory.html', cat_name = category_name,
                               cats = cats, items = items)
    else:
        return render_template('privatecategory.html', cat_name = category_name,
                               cats = cats, items = items)
             


# Route for /catalog/<Category Name>/<Item Name>/
@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItem(category_name, item_name):
    item = session.query(Item).filter_by(
                name = item_name).one()
    if 'username' not in login_session:
        return render_template('publicitem.html', item=item)
    else:
        email = login_session['email']
        if item.user_id == getUserID(email):
            return render_template('authitem.html', item=item)
        else:
            return render_template('privateitem.html', item=item)

# Route for editing items.
# /catalog/<Item Name>/edit/
@app.route('/catalog/<string:item_name>/edit/', methods=['GET', 'POST'])
def editItem(item_name):
    item = session.query(Item).filter_by(
                name=item_name).one()
    cats = session.query(Category)
    if request.method=='POST':
        # Since category is a drop down, it will be selected.
        # In case name and description are blank, they won't be edited.
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        item.category_name = request.form['category']
        session.add(item)
        session.commit()
        flash('Item edited successfully: %s' % item.name)
        return redirect(url_for('showCatsAndItems'))
    else:
        if 'username' in login_session:
            if item.user_id == login_session['user_id']:
                return render_template('edititem.html', item=item, cats=cats)
            else:
                flash('Only the creators of items can edit them.')
                return render_template('privateitem.html', item=item)
        else:
            flash('Only the creators of items can edit them.')
            return render_template('publicitem.html', item=item)


# Checks if an item name exists
def isUnique(newItemName):
    existingItem = session.query(Item).filter_by(name=newItemName).all()
    return len(existingItem) == 0


# Route for adding items.
# /catalog/new/
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newItem():
    cats = session.query(Category)
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if (request.form['name'] and request.form['description'] and
            request.form['category_name'] and isUnique(request.form['name'])):
            name=request.form['name']
            category_name=request.form['category_name']
            newItem = Item(
                           name = name,
                           user_id=login_session['user_id'],
                           description=request.form['description'],
                           category_name=category_name)
            if not catExists(category_name):
                newCat = Category(name = category_name)
                session.add(newCat)
                session.commit()
            session.add(newItem)
            flash('New item %s successfully Created' % newItem.name)
            session.commit()
            print "Date added: %s " % newItem.dateAdded
            return redirect(url_for('showCatsAndItems'))
        else:
            flash('New items require a unique name, a description, and a category.')
            return redirect(url_for('showCatsAndItems'))
    else:
        return render_template('newitem.html', cats=cats)


# Helper for checking if a category exists

def catExists(someCat):
    cats = session.query(Category)
    isFound = False
    for c in cats:
        if c.name == someCat:
            isFound = True
    return isFound


# Route for deleting items.
@app.route('/catalog/<string:item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(item_name):
    itemToDelete = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'POST':
        category_name = itemToDelete.category_name
        shrinkingCat = session.query(Category).filter_by(name
                                                         = category_name).all()
        numCat = len(shrinkingCat)
        if numCat == 1:
            shrinkingCat = session.query(Category).filter_by(name
                                                             = category_name).one()
            session.delete(shrinkingCat)
        session.delete(itemToDelete)
        flash('%s successfully deleted' % itemToDelete.name)
        session.commit()
        return redirect(url_for('showCatsAndItems'))
    else:
        if itemToDelete.user_id == login_session['user_id']:
            return render_template('deleteitem.html', item=itemToDelete)
        else:
            flash('Only the creators of items can delete them.')
            return render_template('publicitem.html', item=itemToDelete)

# Route for JSON API to show Category and nested Item information
@app.route('/catalog.json')
def catItemJSON():
    cats = session.query(Category).all()
    return jsonify(Category=[c.serialize for c in cats])

# Route for XML API to show Category and nested Item information
@app.route('/catalog.xml')
def catItemXML():
    cats = session.query(Category).all()
    dict = {}
    dict.update(Category=[c.serialize for c in cats])
    xml = dicttoxml.dicttoxml(dict)
    output = parseString(xml)
    return output.toprettyxml()



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)