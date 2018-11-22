#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, \
    jsonify, url_for, flash, make_response
from flask import session as login_session

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from models import Base, Category, CatalogItem, User

import httplib2
import json
import requests
import random
import string

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Reusing the app name from previous project for authentication purposes
APPLICATION_NAME = "Restaurant Menu Application"

# Connect to Database and create database session
engine = create_engine(
    'sqlite:///catalog.db',
    connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/category/item/JSON')
# JSON APIs to view all catalog items
def catalogItemsJSON():
    items = session.query(CatalogItem).all()
    return jsonify(categoryItems=[i.serialize for i in items])


@app.route('/category/<int:category_id>/item/JSON')
# JSON APIs to view catalog items for specific category
def categoryCatalogItemJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).first()
    items = session.query(CatalogItem).filter_by(
        category_id=category_id).all()
    return jsonify(categoryItems=[i.serialize for i in items])


@app.route('/category/item/<int:item_id>/JSON')
# JSON APIs to view specific catalog item data
def CatalogItemJSON(category_id, item_id):
    item = session.query(CatalogItem).filter_by(id=item_id).first()
    return jsonify(category_Item=item.serialize)


@app.route('/category/JSON')
# JSON APIs to view all categories
def CatalogCategoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/category/<int:category_id>/JSON')
# JSON APIs to view specific category
def CatalogCategoryJSON():
    category = session.query(Category).first()
    return jsonify(category=category.serialize)


@app.route('/user/JSON')
# JSON APIs to view all users
def CatalogUsersJSON():
    users = session.query(User).all()
    return jsonify(users=[u.serialize for u in users])


@app.route('/user/<int:user_id>/JSON')
# JSON APIs to view specific user information
def CatalogUserJSON():
    user = session.query(User).filter_by(id=user_id).first()
    return jsonify(user=user.serialize)


def getCategories(items):
    # Create an array with category names which will be concatenated to the
    # catalog items listed in the main view
    categories_with_items = []
    for i in items:
        category = session.query(Category).filter_by(
            id=i.category_id).first()
        categories_with_items.append(category.name)
    return categories_with_items


@app.route('/')
@app.route('/category')
# Show all categories with the latest 10 catalog items added
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).order_by(
        CatalogItem.id.desc()).limit(10).all()
    # Get the category names which will be concatenated to each catalog item
    categories_with_items = getCategories(items=items)
    # Categories will be listed on the first column of the table,
    # items will be concatenaded with categories_with_items and listed
    # in the second column
    return render_template(
        'catalog.html', categories=categories, items=items,
        categories_with_items=categories_with_items)


@app.route('/category/new', methods=['GET', 'POST'])
# Create a new category
def newCategory():
    # If user has not logged in then it will redirected to log in
    if 'username' not in login_session:
        flash('In order to add a new category you must log in')
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    if request.method == 'GET':
        return render_template('newCategory.html')


@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
# Edit a catalog category
def editCategory(category_id):
    # If user has not logged in then it will redirected to log in
    if 'username' not in login_session:
        flash('In order to edit a category you must log in')
        return redirect('/login')
    # Get the category to be edited
    editedCategory = session.query(Category).filter_by(
        id=category_id).first()
    # If user is the owner then he is allowed to edit this item
    if editedCategory.user_id == login_session['user_id']:
        if request.method == 'POST':
            if request.form['name']:
                editedCategory.name = request.form['name']
                session.commit()
                flash('Category successfully edited %s' % editedCategory.name)
                return redirect(url_for('showCategories'))
        if request.method == 'GET':
            return render_template(
                'editCategory.html',
                category=editedCategory)
    # User is not the owner so it is not allowed to make any changes
    else:
        flash('You can not edit this category because you are not the owner')
        return redirect(url_for('showCategories'))


@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
# Delete a category and its catalog items
def deleteCategory(category_id):
    # If user has not logged in then it will redirected to log in
    if 'username' not in login_session:
        flash('In order to delete a category you must log in')
        return redirect('/login')
    # Get the category to be deleted
    categoryToDelete = session.query(Category).filter_by(
        id=category_id).first()
    # If user is the owner then he is allowed to delete this item
    if categoryToDelete.user_id == login_session['user_id']:
        if request.method == 'POST':
            session.delete(categoryToDelete)
            session.query(CatalogItem).filter_by(
                category_id=category_id).delete()
            flash('%s Successfully Deleted' % categoryToDelete.name)
            session.commit()
            return redirect(
                url_for('showCategories', category_id=category_id))
        if request.method == 'GET':
            return render_template(
                'deleteCategory.html',
                category=categoryToDelete)
    # User is not the owner so it is not allowed to make any changes
    else:
        flash('You can\'t delete this category because you are not the owner')
        return redirect(url_for('showCategories'))


@app.route('/category/item/<int:item_id>')
# Show specific catalog item details
def showCatalogItemDetails(item_id):
    item = session.query(CatalogItem).filter_by(id=item_id).first()
    categories = session.query(Category)
    return render_template(
        'catalogItem.html', item=item, categories=categories)


@app.route('/category/<int:category_id>')
@app.route('/category/<int:category_id>/item')
# Show catalog items for a specific category
def showCatalogItem(category_id):
    category = session.query(Category).filter_by(id=category_id).first()
    items = session.query(CatalogItem).filter_by(
        category_id=category_id).all()
    return render_template(
        'categoryCatalogItem.html', items=items, category=category)


@app.route('/category/item/new', methods=['GET', 'POST'])
# Create a new catalog item
def newCatalogItem():
    # If user has not logged in then it will redirected to log in
    if 'username' not in login_session:
        flash('In order to add a new catalog item you must log in')
        return redirect('/login')
    categories = session.query(Category)
    if request.method == 'POST':
        category = session.query(Category).filter_by(
            name=request.form['category']).first()
        newItem = CatalogItem(
            title=request.form['title'],
            description=request.form['description'],
            category_id=category.id, user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Category %s Item Successfully Created' % (newItem.title))
        return redirect(url_for('showCategories'))
    if request.method == 'GET':
        return render_template('newCatalogItem.html', categories=categories)


@app.route('/category/item/<int:item_id>/edit', methods=['GET', 'POST'])
# Edit a catalog item
def editCatalogItem(item_id):
    # If user has not logged in then it will redirected to log in
    if 'username' not in login_session:
        flash('In order to edit a catalog item you must log in')
        return redirect('/login')
    # Get the catalog item to be edited
    editedItem = session.query(CatalogItem).filter_by(id=item_id).first()
    # Get the categories so they are displayed in a list of options
    categories = session.query(Category)
    # If user is the owner then he is allowed to edit this item
    if editedItem.user_id == login_session['user_id']:
        if request.method == 'POST':
            if request.form['title']:
                editedItem.title = request.form['title']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['category']:
                category = session.query(Category).filter_by(
                    name=request.form['category']).first()
                editedItem.category_id = category.id
            session.add(editedItem)
            session.commit()
            flash('Catalog Item Successfully Edited')
            return redirect(url_for('showCategories'))
        if request.method == 'GET':
            return render_template(
                'editCatalogItem.html', item_id=item_id,
                item=editedItem, categories=categories)
    # User is not the owner so it is not allowed to make any changes
    else:
        flash('You can\'t edit this item because you are not the owner')
        return redirect(url_for('showCategories'))


@app.route('/category/item/<int:item_id>/delete', methods=['GET', 'POST'])
# Delete a catalog item
def deleteCatalogItem(item_id):
    # If user has not logged in then it will redirected to log in
    if 'username' not in login_session:
        flash('In order to delete a catalog item you must log in')
        return redirect('/login')
    # Get the catalog item to be deleted
    itemToDelete = session.query(CatalogItem).filter_by(id=item_id).first()
    # Get the categories so they are displayed in a list of options
    categories = session.query(Category)
    # If user is the owner then he is allowed to delete this item
    if itemToDelete.user_id == login_session['user_id']:
        if request.method == 'POST':
            category_id = itemToDelete.category_id
            session.delete(itemToDelete)
            session.commit()
            flash('Category Item Successfully Deleted')
            return redirect(url_for('showCategories'))
        if request.method == 'GET':
            return render_template(
                'deleteCatalogItem.html', item=itemToDelete,
                categories=categories)
    # User is not the owner so it is not allowed to make any changes
    else:
        flash('You can\'t delete this item because you are not the owner')
        return redirect(url_for('showCategories'))


@app.route('/login')
# Create anti-forgery state token to login user with a third party system
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html',  STATE=state)


@app.route('/fbconnect', methods=['POST'])
# Log in user using facebook
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=\
        fb_exchange_token&client_id=%s&client_secret=%s\
        &fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange
        we have to split the token first on commas and select the first index
        which gives us the key : value for the server access token then we
        split it on colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used directly in the
        graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')
    url = 'https://graph.facebook.com/v2.8/me?access_token=%s\
        &fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to
    # properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s\
        &redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # See if user exists
    user_id = getUserID(login_session['email'])
    # If user does not exist in database then it is inserted
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src = "'
    output += login_session['picture']
    output += ' " style="width: 300px; height: 300px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
# Logout from facebook
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
        % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
# Log in using google
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
        oauth_flow = flow_from_clientsecrets(
            'client_secrets.json', scope='')
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
        return response

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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # See if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    # If user does not exist then insert it to the database
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src = "'
    output += login_session['picture']
    output += ' " style="width: 300px; height: 300px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    # add user to the database
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    # get user_id based on its email for authentication purposes
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except IOerror as err:
        print "Error: %s" % err
        return None


@app.route('/gdisconnect')
# disconnect from google
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
                json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
# Disconnect based on provider
def disconnect():
    # if provider then users is logged in
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            # this data is not deleted in above function
            del login_session['facebook_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
