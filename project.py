from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, CatalogItem, User

from flask import session as login_session
import random, string

import httplib2
import json
#from flask import make_response
import requests

app = Flask(__name__)

#Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def getUserId():
    user = session.query(User).first()
    return user.id

# Temporary login funtion to add 1 user if DB empty
@app.route('/login')
def login():
    user = session.query(User).first()
    if user == None:
        newUser = User(name = 'salvador')
        session.add(newUser)
        session.commit()
    return

#JSON APIs to view all catalog items 
@app.route('/category/item/JSON')
def catalogItemsJSON():
    items = session.query(CatalogItem).all()
    return jsonify(categoryItems=[i.serialize for i in items])

#JSON APIs to view catalog items information for specific category
@app.route('/category/<int:category_id>/item/JSON')
def categoryCatalogItemJSON(category_id):
    category = session.query(Category).filter_by(id = category_id).first()
    items = session.query(CatalogItem).filter_by(category_id = category_id).all()
    return jsonify(categoryItems=[i.serialize for i in items])

#JSON APIs to view catalog item Information
@app.route('/category/item/<int:item_id>/JSON')
def CatalogItemJSON(category_id, item_id):
    item = session.query(CatalogItem).filter_by(id = item_id).first()
    return jsonify(category_Item = item.serialize)

#JSON APIs to view all catalog categories information
@app.route('/category/JSON')
def CatalogCategoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories= [r.serialize for r in categories])

#JSON APIs to view catalog category information
@app.route('/category/<int:category_id>/JSON')
def CatalogCategoryJSON():
    category = session.query(Category).first()
    return jsonify(category = category.serialize)

#JSON APIs to view users information
@app.route('/user/JSON')
def CatalogUsersJSON():
    users = session.query(User).all()
    return jsonify(users= [u.serialize for u in users])

#JSON APIs to view user information
@app.route('/user/<int:user_id>/JSON')
def CatalogUserJSON():
    user = session.query(User).filter_by(id = user_id).first()
    return jsonify(user= user.serialize)


#Show all catalog categories
@app.route('/')
@app.route('/category')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).order_by(asc(CatalogItem.title))
    return render_template('categories.html', categories = categories, items = items)

#Create a new catalog category
@app.route('/category/new', methods=['GET','POST'])
def newCategory():
    if request.method == 'POST':
        newCategory = Category(name = request.form['name'], user_id = getUserId())
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    if request.method == 'GET':
        return render_template('newCategory.html')

#Edit a catalog category
@app.route('/category/<int:category_id>/edit', methods = ['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(Category).filter_by(id = category_id).first()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            session.commit()
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCategories'))
    if request.method == 'GET':
        return render_template('editCategory.html', category = editedCategory)

#Delete a catalog category
@app.route('/category/<int:category_id>/delete', methods = ['GET','POST'])
def deleteCategory(category_id):
    categoryToDelete = session.query(Category).filter_by(id = category_id).first()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showCategories', category_id = category_id))
    if request.method == 'GET':
        return render_template('deleteCategory.html',category = categoryToDelete)

#Show catalog item details 
@app.route('/category/item/<int:item_id>')
def showCatalogItemDetails(item_id):
    item = session.query(CatalogItem).filter_by(id = item_id).first()
    return render_template('catalogItemDetails.html', item = item)

#Show catalog items of a specific category
@app.route('/category/<int:category_id>')
@app.route('/category/<int:category_id>/item')
def showCatalogItem(category_id):
    category = session.query(Category).filter_by(id = category_id).first()
    items = session.query(CatalogItem).filter_by(category_id = category_id).all()
    return render_template('catalogItem.html', items = items, category = category)

#Create a new catalog item
@app.route('/item/new',methods=['GET','POST'])
def newCatalogItem():
    categories = session.query(Category)
    if request.method == 'POST':
        category = session.query(Category).filter_by(name=request.form['category']).first()
        newItem = CatalogItem(title = request.form['title'], description = request.form['description'], 
        category_id = category.id, user_id = getUserId())
        session.add(newItem)
        session.commit()
        flash('New Category %s Item Successfully Created' % (newItem.title))
        return redirect(url_for('showCatalogItem', category_id=category.id))
    if request.method == 'GET':
      return render_template('newCatalogItem.html', categories = categories)

#Edit a catalog item
@app.route('/item/<int:item_id>/edit', methods=['GET','POST'])
def editCatalogItem(item_id):
    editedItem = session.query(CatalogItem).filter_by(id = item_id).first()
    categories = session.query(Category)
    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            category = session.query(Category).filter_by(name=request.form['category']).first()
            editedItem.category_id = category.id
        session.add(editedItem)
        session.commit() 
        flash('Catalog Item Successfully Edited')
        return redirect(url_for('showCatalogItem', category_id=category.id))
    if request.method == 'GET':
        return render_template('editCatalogItem.html', item_id = item_id, item = editedItem, categories = categories)


#Delete a catalog item
@app.route('/item/<int:item_id>/delete', methods = ['GET','POST'])
def deleteCatalogItem(item_id):
    itemToDelete = session.query(CatalogItem).filter_by(id = item_id).first()
    categories = session.query(Category) 
    if request.method == 'POST':
        category_id=itemToDelete.category_id
        session.delete(itemToDelete)
        session.commit()
        flash('Category Item Successfully Deleted')
        return redirect(url_for('showCatalogItem', category_id=category_id))
    if request.method == 'GET':
        return render_template('deleteCatalogItem.html', item = itemToDelete, categories = categories)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    login()
    app.run(host = '0.0.0.0', port = 8000)
