## Catalog Project
**Catalog** is a _udacity_ project implementing a web application that provides a list of items within a variety of categories and integrate third party user registration and authentication (_google_, _facebook_). Authenticated users should have the ability to post, edit, and delete their own items.


## How To Run The Program
**Catalog** has been tested using _python 3.6.3_, it is recommended to use that version. You can try other version and program may still run.
To run the program just open a terminal and run: `python catalog.py`


## Catalog Design
**Catalog** code design follows CRUD functionality for categories and catalog items and each functionality has a corresponding `html` template to display information (read) or interact with the user (create/update/delete):

**Categories:**

  - **C**reate: to add a new category
  - **R**ead: to display all categories
  - **U**pdate: to edit a category (name)
  - **D**elete: to delete a category

**Catalog items:**

  - **C**reate: to add a new catalog item
  - **R**ead: to display all catalog items in a category
  - **U**pdate: to edit a catalog item (title, description, category)
  - **D**elete: to delete a catalog item


The application also provides **JSON** endpoints to retrieve information from the database.

**Categories:**

  - `/catalog/JSON` to display all categories
  - `/catalog/<int:category_id>/JSON` to display specific category (`category_id`)

**Catalog items:**

  - `/catalog/item/JSON` to display all catalog items
  - `/catalog/<int:category_id>/item/JSON` to display catalog items in a specific category (`category_id`)
  - `/catalog/<string:category_name>/item/JSON` to display catalog items in a specific category (`category_name`)
  - `/catalog/<int:category_id>/item/<int:item_id>/JSON` to display specific catalog item (`item_id`) in a category (`category_id`)
  - `/catalog/<string:category_name>/item/<string:item_title>/JSON` to display specific catalog item (`item_title`) in a category (`category_name`)

**Users:**

  - `/catalog/user/JSON` to display all users information
  - `/catalog/user/<int:user_id>/JSON` to display information of an specific user (`user_id`)


**Catalog** supports authentication using _google_ and _facebook_.  If user is not logged in, it can only read information from the database. After it logged in, it can post, update and delete records it owns.

## Catalog Navigation
**Catalog** navigation is intuitive, user starts at homepage ('/' or '/catalog') where a table is displayed listing all the categories and the latest 10 catalog items added. From here the user can click any category or any catalog item to display its related information. Each page after the homepage will have buttons letting the user know what operations are allowed.
User must pay attention to messages displayed below the blue main bar (where "login/logout" button is located), it will tell user of records successfully being created/updated/deleted or the failure of do so.