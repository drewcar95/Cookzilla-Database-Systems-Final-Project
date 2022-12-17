# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors

# for uploading photo:
from app import app
#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

import bcrypt

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


# Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3336,
                       user='root',
                       password='root',
                       db='Cookzilla',
                       charset='utf8',
                       cursorclass=pymysql.cursors.DictCursor)


def allowed_image(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


def allowed_image_filesize(filesize):

    if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False


# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

# Define route for login


@app.route('/login')
def login():
    return render_template('login.html')

# Define route for register


@app.route('/register')
def register():

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = 'select * from unit where type = %s'
    cursor.execute(query, 'solid')
    sunit_data = cursor.fetchall()

    query = 'select * from unit where type = %s'
    cursor.execute(query, 'liquid')
    lunit_data = cursor.fetchall()

    cursor.close()

    return render_template('register.html', sunit_data=sunit_data, lunit_data=lunit_data)


@app.route('/post')
def post():
    return render_template('post.html')

# Authenticates the login


@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    # cursor used to send queries
    #cursor = conn.cursor()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # executes query
    '''query = 'SELECT * FROM user WHERE username = %s and password = %s'
    #cursor.execute(query, (username, password))
    cursor.execute(query, (username, hashedPassword))
    #stores the results in a variable
    data = cursor.fetchone()'''

    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))

    if cursor.rowcount != 1:
        error = 'Invalid username'
        return render_template('login.html', error=error)

    #user = cursor[0]['password']
    for row in cursor:
        user_pass = row['password']
    passwordBytes = password.encode('utf-8')
    hashedPWInBytes = user_pass.encode('utf-8')
    passwordMatches = bcrypt.checkpw(passwordBytes, hashedPWInBytes)

    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None

    # if(data):
    if(passwordMatches):
        # creates a session for the the user
        # session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

# Authenticates the register


@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    profile = request.form['profile']
    sUnitPreference = request.form['sUnitPreference']
    lUnitPreference = request.form['lUnitPreference']

    passwordBytes = password.encode('utf-8')
    hashedPassword = bcrypt.hashpw(passwordBytes, bcrypt.gensalt())

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
        #cursor.execute(ins, (username, password))
        cursor.execute(ins, (username, hashedPassword, fname, lname,
                       email, profile, sUnitPreference, lUnitPreference))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT recipeID, title, numServings FROM recipe WHERE postedBy = %s ORDER BY recipeID DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()

    query2 = 'SELECT avg(stars) as userAVG FROM Recipe NATURAL JOIN REVIEW WHERE postedBY = %s'
    cursor.execute(query2, user)
    userAVG = cursor.fetchall()
    cursor.close()
    
    return render_template('home.html', username=user, posts=data, userAVG=userAVG)
    #cursor.close()
    #return render_template('home.html', username=user, posts=data, userAVG=userAVG)
    # return render_template('home.html', username=user)


@app.route('/postRecipe', methods=['GET', 'POST'])
def postRecipe():
    username = session['username']
    cursor = conn.cursor()
    title = request.form['title']
    numServings = request.form['servings']
    query = 'INSERT INTO recipe (title, numServings, postedBy) VALUES(%s, %s, %s)'
    cursor.execute(query, (title, numServings, username))
    conn.commit()

    query = 'select * from recipe where recipeID = (select max(recipeID) from recipe)'
    cursor.execute(query)
    for row in cursor:
        recipeID = row['recipeID']
        title = row['title']
        numServings = row['numServings']

    '''query = 'select * from ingredient'
    cursor.execute(query)
    ingr_data = cursor.fetchall()'''

    query = 'select * from unit'
    cursor.execute(query)
    unit_data = cursor.fetchall()

    cursor.close()

    session['recipeID'] = recipeID
    session['title'] = title
    session['numServings'] = numServings
    session['stepNo'] = 0

    return render_template('recipeStepsTags.html', recipeID=recipeID, title=title, numServings=numServings, stepNo=0, unit_data=unit_data)
    # return redirect(url_for('recipeStepsTags'))


@app.route('/recipeSteps', methods=['GET', 'POST'])
def recipeSteps():
    stepDescription = request.form['stepDescription']
    recipeID = session['recipeID']
    stepNo = session['stepNo']
    title = session['title']
    numServings = session['numServings']
    stepNo += 1

    cursor = conn.cursor()
    query = 'insert into step VALUES(%s, %s, %s)'
    cursor.execute(query, (stepNo, recipeID, stepDescription))
    conn.commit()

    query = 'select * from recipeingredient where recipeID = %s'
    cursor.execute(query, (recipeID))
    ingredients = cursor.fetchall()

    query = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query, (recipeID))
    data = cursor.fetchall()

    query = 'select * from recipetag where recipeID = %s'
    cursor.execute(query, (recipeID))
    tagdata = cursor.fetchall()

    query = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query, (recipeID))
    imgdata = cursor.fetchall()

    query = 'select * from ingredient'
    cursor.execute(query)
    ingr_data = cursor.fetchall()

    query = 'select * from unit'
    cursor.execute(query)
    unit_data = cursor.fetchall()

    cursor.close()
    session['stepNo'] = stepNo

    return render_template('recipeStepsTags.html', recipeID=recipeID, title=title, numServings=numServings,
                           steps=data, tags=tagdata, ingredients=ingredients, unit_data=unit_data, images=imgdata)


@app.route('/recipeTags', methods=['GET', 'POST'])
def recipeTags():
    tagText = request.form['tagText']
    recipeID = session['recipeID']
    title = session['title']
    numServings = session['numServings']

    cursor = conn.cursor()
    query = 'insert into recipetag VALUES(%s, %s)'
    cursor.execute(query, (recipeID, tagText))
    conn.commit()

    query = 'select * from recipeingredient where recipeID = %s'
    cursor.execute(query, (recipeID))
    ingredients = cursor.fetchall()

    query = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query, (recipeID))
    data = cursor.fetchall()

    query = 'select * from recipetag where recipeID = %s'
    cursor.execute(query, (recipeID))
    tagdata = cursor.fetchall()

    query = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query, (recipeID))
    imgdata = cursor.fetchall()

    query = 'select * from ingredient'
    cursor.execute(query)
    ingr_data = cursor.fetchall()

    query = 'select * from unit'
    cursor.execute(query)
    unit_data = cursor.fetchall()

    cursor.close()

    return render_template('recipeStepsTags.html', recipeID=recipeID, title=title, numServings=numServings,
                           steps=data, tags=tagdata, ingredients=ingredients, unit_data=unit_data, images=imgdata)


@app.route('/recipeIngredients', methods=['GET', 'POST'])
def recipeIngredients():
    iName = request.form['ingredient']
    unitName = request.form['unit']
    amount = request.form['amount']
    restrictionDesc = request.form['restriction']
    recipeID = session['recipeID']
    title = session['title']
    numServings = session['numServings']

    cursor = conn.cursor()
    query = "SELECT * FROM ingredient WHERE iName like %s"
    cursor.execute(query, (iName))
    data = cursor.fetchone()
    error = None
    if(data):
        # If the previous query returns data, then user exists
        query = 'insert into recipeingredient VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (recipeID, iName, unitName, amount))

        query = 'update restrictions set restrictionDesc = %s where iName = %s'
        cursor.execute(query, (restrictionDesc, iName))
    else:
        query = 'insert into ingredient VALUES(%s, %s)'
        cursor.execute(query, (iName, 'null'))

        query = 'insert into restrictions VALUES(%s, %s)'
        cursor.execute(query, (iName, restrictionDesc))

        query = 'insert into recipeingredient VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (recipeID, iName, unitName, amount))

    conn.commit()

    query = 'select * from recipeingredient where recipeID = %s'
    cursor.execute(query, (recipeID))
    ingredients = cursor.fetchall()

    query = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query, (recipeID))
    data = cursor.fetchall()

    query = 'select * from recipetag where recipeID = %s'
    cursor.execute(query, (recipeID))
    tagdata = cursor.fetchall()

    query = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query, (recipeID))
    imgdata = cursor.fetchall()

    query = 'select * from ingredient'
    cursor.execute(query)
    ingr_data = cursor.fetchall()

    query = 'select * from unit'
    cursor.execute(query)
    unit_data = cursor.fetchall()

    cursor.close()

    return render_template('recipeStepsTags.html', recipeID=recipeID, title=title, numServings=numServings,
                           steps=data, tags=tagdata, ingredients=ingredients, unit_data=unit_data, images=imgdata)


@app.route('/recipeImages', methods=['GET', 'POST'])
def recipeImages():
    pictureURL = request.form['newImage']
    recipeID = session['recipeID']
    title = session['title']
    numServings = session['numServings']

    cursor = conn.cursor()
    query = 'insert into RecipePicture VALUES(%s, %s)'
    cursor.execute(query, (recipeID, pictureURL))
    conn.commit()

    query = 'select * from recipeingredient where recipeID = %s'
    cursor.execute(query, (recipeID))
    ingredients = cursor.fetchall()

    query = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query, (recipeID))
    data = cursor.fetchall()

    query = 'select * from recipetag where recipeID = %s'
    cursor.execute(query, (recipeID))
    tagdata = cursor.fetchall()

    query = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query, (recipeID))
    imgdata = cursor.fetchall()

    query = 'select * from ingredient'
    cursor.execute(query)
    ingr_data = cursor.fetchall()

    query = 'select * from unit'
    cursor.execute(query)
    unit_data = cursor.fetchall()

    cursor.close()

    return render_template('recipeStepsTags.html', recipeID=recipeID, title=title, numServings=numServings,
                           steps=data, tags=tagdata, ingredients=ingredients, unit_data=unit_data, images=imgdata)


@app.route('/recipeImages', methods=['GET', 'POST'])
def recipeRelated():
    relatedRecipeID = request.form['relatedRecipeID']
    recipeID = session['recipeID']
    title = session['title']
    numServings = session['numServings']

    cursor = conn.cursor()
    query = 'insert into RecipePicture VALUES(%s, %s)'
    cursor.execute(query, (recipeID, relatedRecipeID))
    conn.commit()

    query = 'select * from recipeingredient where recipeID = %s'
    cursor.execute(query, (recipeID))
    ingredients = cursor.fetchall()

    query = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query, (recipeID))
    data = cursor.fetchall()

    query = 'select * from recipetag where recipeID = %s'
    cursor.execute(query, (recipeID))
    tagdata = cursor.fetchall()

    query = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query, (recipeID))
    imgdata = cursor.fetchall()

    query = 'select * from ingredient'
    cursor.execute(query)
    ingr_data = cursor.fetchall()

    query = 'select * from unit'
    cursor.execute(query)
    unit_data = cursor.fetchall()

    cursor.close()

    return render_template('recipeStepsTags.html', recipeID=recipeID, title=title, numServings=numServings,
                           steps=data, tags=tagdata, ingredients=ingredients, unit_data=unit_data, images=imgdata)


@app.route('/postSummary')
def postSummary():
    recipeID = session['recipeID']
    username = session['username']
    cursor = conn.cursor()
    query = 'select * from recipe where recipeID = %s'
    cursor.execute(query, (recipeID))
    for row in cursor:
        recipeID = row['recipeID']
        title = row['title']
        numServings = row['numServings']

    query = 'select * from person where userName = %s'
    cursor.execute(query, (username))
    for row in cursor:
        sUnitPreference = row['sUnitPreference']
        lUnitPreference = row['lUnitPreference']

    #query = 'select * from recipeingredient where recipeID = %s'
    query = 'select a.*, b.destinationUnit as preferredUnit, amount * ratio as convertamount from recipeingredient a \
                left join (select * from unitconversion where destinationUnit in (%s,%s)) b \
                on a.unitName = b.sourceUnit where recipeID = %s'
    cursor.execute(query, (sUnitPreference, lUnitPreference, recipeID))
    ingredients = cursor.fetchall()

    query = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query, (recipeID))
    data = cursor.fetchall()

    query = 'select * from recipetag where recipeID = %s'
    cursor.execute(query, (recipeID))
    tagdata = cursor.fetchall()

    query = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query, (recipeID))
    imgdata = cursor.fetchall()

    query = 'select * from unitconversion'
    cursor.execute(query)
    unitconvdata = cursor.fetchall()

    cursor.close()

    return render_template('postSummary.html', recipeID=recipeID, title=title, numServings=numServings,
                           steps=data, tags=tagdata, ingredients=ingredients, images=imgdata, unitconvdata=unitconvdata)


@app.route('/postSummary2', methods=['GET', 'POST'])
def postSummary2():
    recipeID = session['recipeID']
    unit1 = request.form['unit1']
    unit2 = request.form['unit2']
    username = session['username']

    cursor = conn.cursor()

    query = 'select * from unitconversion where sourceUnit = %s and destinationUnit = %s'
    cursor.execute(query, (unit1, unit2))
    ratios = cursor.fetchall()

    for row in ratios:
        ratio = row['ratio']

    query = 'select * from person where userName = %s'
    cursor.execute(query, (username))
    for row in cursor:
        sUnitPreference = row['sUnitPreference']
        lUnitPreference = row['lUnitPreference']

    query = 'select * from recipe where recipeID = %s'
    cursor.execute(query, (recipeID))
    for row in cursor:
        recipeID = row['recipeID']
        title = row['title']
        numServings = row['numServings']

    #query = 'select * from recipeingredient where recipeID = %s'
    query = 'select a.*, b.destinationUnit as preferredUnit, amount * ratio as convertamount from recipeingredient a \
                left join (select * from unitconversion where destinationUnit in (%s,%s)) b \
                on atNa.unime = b.sourceUnit where recipeID = %s'
    cursor.execute(query, (sUnitPreference, lUnitPreference, recipeID))
    ingredients = cursor.fetchall()

    for row in ingredients:
        if row['unitName'] == unit1:
            row['unit'] = unit2
            row['amount'] = row['amount'] * ratio

    query = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query, (recipeID))
    data = cursor.fetchall()

    query = 'select * from recipetag where recipeID = %s'
    cursor.execute(query, (recipeID))
    tagdata = cursor.fetchall()

    query = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query, (recipeID))
    imgdata = cursor.fetchall()

    query = 'select * from unitconversion'
    cursor.execute(query)
    unitconvdata = cursor.fetchall()

    cursor.close()

    return render_template('postSummary.html', recipeID=recipeID, title=title, numServings=numServings,
                           steps=data, tags=tagdata, ingredients=ingredients, images=imgdata, unitconvdata=unitconvdata)


@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/searchForRecipe', methods = ['POST', 'GET'])
def searchForRecipe():
    recipetitle = request.form['recipetitle']
    tag = request.form['tags']
    rating = request.form['rating']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT recipeID, title, postedBy, avg(stars) as avg FROM Recipe NATURAL JOIN Review GROUP BY recipeID HAVING avg >= %s'
    cursor.execute(query, (rating))
    avgVals = cursor.fetchall()

    view = 'SELECT DISTINCT recipeID, title, postedBy, avg(stars) as avg FROM Recipe NATURAL JOIN RecipeTag NATURAL JOIN Review WHERE (title = %s AND tagText = %s) OR (title = %s OR tagText = %s) GROUP BY recipeID HAVING avg >= %s'
    cursor.execute(view, (recipetitle, tag, recipetitle, tag, rating))
    view = cursor.fetchall()

    if(tag):
        if(view):
            Recipes = view
            return render_template('searchForRecipe.html', Recipes=Recipes)
        else:
            error = 'No Results Found'
            return render_template('searchForRecipe.html', error=error)
        
    elif(recipetitle):
        if(view):
            Recipes = view
            return render_template('searchForRecipe.html', Recipes=Recipes)
        else:
            error = 'No Results Found'
            return render_template('searchForRecipe.html', error=error)

        
        
    elif(rating):
        Recipes = avgVals
        return render_template('searchForRecipe.html', Recipes=Recipes)
    else:
        error = 'No Results Found'
        return render_template('searchForRecipe.html', error=error)

@app.route('/searchbyIngredient')
def searchbyIngredient():
    return render_template('searchbyIngredient.html')

@app.route('/ingredientSearch', methods = ['POST', 'GET'])
def ingredientSearch():
    ingredient = request.form['ingredient']
    cursor = conn.cursor();

    query = 'SELECT DISTINCT recipeID, title, postedBy, avg(stars) as avg FROM Recipe NATURAL JOIN RecipeIngredient NATURAL JOIN Review WHERE iName = %s GROUP BY recipeID'
    cursor.execute(query, (ingredient))
    Recipes = cursor.fetchall()
    cursor.close()

    if(Recipes):
        return render_template('searchForRecipe.html', Recipes=Recipes)
        
    else:
        error = 'No Results Found'
        return render_template('searchForRecipe.html', error=error)


@app.route('/viewRecipe')
def viewRecipe():
    recipeID = request.args['recipeID']
    session['recipeID'] = recipeID
    username = session['username']
    cursor = conn.cursor();
    

    query1 = 'SELECT * FROM Recipe WHERE recipeID = %s'
    cursor.execute(query1, (recipeID))
    recipedata = cursor.fetchall()

    query2 = 'SELECT DISTINCT * FROM Review WHERE recipeID = %s'
    cursor.execute(query2, (recipeID))
    revs = cursor.fetchall()

    query3 = 'select * from person where userName = %s'
    cursor.execute(query3, (username))
    for row in cursor:
        sUnitPreference = row['sUnitPreference']
        lUnitPreference = row['lUnitPreference']

    #query = 'select * from recipeingredient where recipeID = %s'
    query4 = 'select a.*, b.destinationUnit as preferredUnit, amount * ratio as convertamount from recipeingredient a \
                left join (select * from unitconversion where destinationUnit in (%s,%s)) b \
                on a.unitName = b.sourceUnit where recipeID = %s'
    cursor.execute(query4, (sUnitPreference, lUnitPreference, recipeID))
    ingredients = cursor.fetchall()

    query5 = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query5, (recipeID))
    stepdata = cursor.fetchall()

    query6 = 'select * from recipetag where recipeID = %s'
    cursor.execute(query6, (recipeID))
    tagdata = cursor.fetchall()

    query7 = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query7, (recipeID))
    imgdata = cursor.fetchall()

    query8 = 'select * from unitconversion'
    cursor.execute(query8)
    unitconvdata = cursor.fetchall()


    return render_template('viewRecipe.html', recipedata = recipedata, recipeID = recipeID, revs = revs, stepdata = stepdata, tagdata=tagdata, imgdata=imgdata, ingredients = ingredients,unitconvdata=unitconvdata)

@app.route('/viewRecipe2', methods = ['GET', 'POST'])
def viewRecipe2():
    recipeID = session['recipeID']
    unit1 = request.form['unit1']
    unit2 = request.form['unit2']
    username = session['username']
    cursor = conn.cursor();

    query1 = 'SELECT * FROM Recipe WHERE recipeID = %s'
    cursor.execute(query1, (recipeID))
    recipedata = cursor.fetchall()

    query = 'select * from unitconversion where sourceUnit = %s and destinationUnit = %s'
    cursor.execute(query, (unit1, unit2))
    ratios = cursor.fetchall()

    for row in ratios:
        ratio = row['ratio']

    query2 = 'SELECT DISTINCT * FROM Review WHERE recipeID = %s'
    cursor.execute(query2, (recipeID))
    revs = cursor.fetchall()

    query3 = 'select * from person where userName = %s'
    cursor.execute(query3, (username))
    for row in cursor:
        sUnitPreference = row['sUnitPreference']
        lUnitPreference = row['lUnitPreference']

    #query = 'select * from recipeingredient where recipeID = %s'
    query4 = 'select a.*, b.destinationUnit as preferredUnit, amount * ratio as convertamount from recipeingredient a \
                left join (select * from unitconversion where destinationUnit in (%s,%s)) b \
                on a.unitName = b.sourceUnit where recipeID = %s'
    cursor.execute(query4, (sUnitPreference, lUnitPreference, recipeID))
    ingredients = cursor.fetchall()

    for row in ingredients:
        if row['unitName'] == unit1:
            row['unit'] = unit2
            row['amount'] = row['amount'] * ratio

    query5 = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query5, (recipeID))
    stepdata = cursor.fetchall()

    query6 = 'select * from recipetag where recipeID = %s'
    cursor.execute(query6, (recipeID))
    tagdata = cursor.fetchall()

    query7 = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query7, (recipeID))
    imgdata = cursor.fetchall()

    query8 = 'select * from unitconversion'
    cursor.execute(query8)
    unitconvdata = cursor.fetchall()
    

    return render_template('viewRecipe.html', recipedata = recipedata, recipeID = recipeID, revs = revs, stepdata = stepdata, tagdata=tagdata, imgdata=imgdata, ingredients = ingredients,unitconvdata=unitconvdata)

@app.route('/review', methods = ['GET','POST'])
def review():
    recipeID = session['recipeID']
    return render_template('review.html', recipeID = recipeID)

@app.route('/postReview', methods=['GET', 'POST'])
def postReview():
    username = session['username']
    recipeID = session['recipeID']
    cursor = conn.cursor();
    reviewTitle = request.form['reviewTitle']
    desc = request.form['review']
    rating = request.form['rating']

    insertquery = 'INSERT INTO Review VALUES(%s,%s,%s,%s,%s)'
    cursor.execute(insertquery, (username, recipeID, reviewTitle, desc, rating))
    conn.commit()

    query1 = 'SELECT * FROM Recipe WHERE recipeID = %s'
    cursor.execute(query1, (recipeID))
    recipedata = cursor.fetchall()

    query2 = 'SELECT DISTINCT * FROM Review WHERE recipeID = %s'
    cursor.execute(query2, (recipeID))
    revs = cursor.fetchall()

    query3 = 'select * from person where userName = %s'
    cursor.execute(query3, (username))
    for row in cursor:
        sUnitPreference = row['sUnitPreference']
        lUnitPreference = row['lUnitPreference']

    #query = 'select * from recipeingredient where recipeID = %s'
    query4 = 'select a.*, b.destinationUnit as preferredUnit, amount * ratio as convertamount from recipeingredient a \
                left join (select * from unitconversion where destinationUnit in (%s,%s)) b \
                on a.unitName = b.sourceUnit where recipeID = %s'
    cursor.execute(query4, (sUnitPreference, lUnitPreference, recipeID))
    ingredients = cursor.fetchall()

    query5 = 'select * from step where recipeID = %s order by stepNo'
    cursor.execute(query5, (recipeID))
    stepdata = cursor.fetchall()

    query6 = 'select * from recipetag where recipeID = %s'
    cursor.execute(query6, (recipeID))
    tagdata = cursor.fetchall()

    query7 = 'select * from RecipePicture where recipeID = %s'
    cursor.execute(query7, (recipeID))
    imgdata = cursor.fetchall()

    query8 = 'select * from unitconversion'
    cursor.execute(query8)
    unitconvdata = cursor.fetchall()

    cursor.close()

    return render_template('viewRecipe.html', recipedata = recipedata, recipeID = recipeID, revs = revs, stepdata = stepdata, tagdata=tagdata, imgdata=imgdata, ingredients = ingredients,unitconvdata=unitconvdata)


@app.route('/select_blogger')
def select_blogger():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT DISTINCT userName FROM Person WHERE userName != %s'
    cursor.execute(query,(username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)


@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor()

    query1 = 'SELECT DISTINCT recipeID, title FROM Recipe WHERE postedBY = %s ORDER BY recipeID DESC'
    cursor.execute(query1, poster)
    data = cursor.fetchall()

    query2 = 'SELECT avg(stars) as userAVG FROM Recipe NATURAL JOIN REVIEW WHERE postedBY = %s'
    cursor.execute(query2, poster)
    userAVG = cursor.fetchall()

    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data, userAVG=userAVG)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            return redirect('/')
        else:
            flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
            return redirect(request.url)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############
###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############
###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############
###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############

# Join or Create a group
@app.route('/group')
def group():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT gName, gCreator, gDesc FROM Group ORDER BY gName'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('group.html', username=user, posts=data)


@app.route('/joinGroup', methods=['GET', 'POST'])
def joinGroup():
    # grabs information from the forms
    user = session['username']
    memberName = request.form['memberName']
    gName = request.form['gName']
    gCreator = request.form['gCreator']
    cursor2 = conn.cursor()
    query2 = 'SELECT gName, gCreator, gDesc FROM Group ORDER BY gName'
    cursor2.execute(query2)
    data2 = cursor2.fetchall()

    cursor = conn.cursor()
    query = 'SELECT * FROM GroupMembership WHERE memberName = %s and gName = %s and gCreator = %s'
    cursor.execute(query, (memberName, gName, gCreator))
    data = cursor.fetchone()
    error1 = None
    remind1 = None

    if(data):
        error1 = "You have already joined this Group!"
        return render_template('group.html', error1=error1, username=user, posts=data2)
    else:
        query = 'INSERT INTO GroupMembership VALUES(%s, %s, %s)'
        cursor.execute(query, (memberName, gName, gCreator))
        conn.commit()
        cursor.close()
        remind1 = "You have joined this Group successfully!"
        return render_template('group.html', remind1=remind1, username=user, posts=data2)


@app.route('/CreateGroup', methods=['GET', 'POST'])
def CreateGroup():
    # grabs information from the forms
    user = session['username']
    gName = request.form['gName']
    gDesc = request.form['gDesc']
    cursor2 = conn.cursor()
    query2 = 'SELECT gName, gCreator, gDesc FROM Group ORDER BY gName'
    cursor2.execute(query2)
    data2 = cursor2.fetchall()

    cursor = conn.cursor()
    query = 'SELECT gName FROM Group WHERE gCreator = %s and gName = %s'
    cursor.execute(query, (user, gName))
    data = cursor.fetchone()
    error2 = None
    remind2 = None

    if(data):
        error2 = "You have already created this Group!"
        return render_template('group.html', error2=error2, username=user, posts=data2)
    else:
        query = 'INSERT INTO Group VALUES(%s, %s, %s)'
        cursor.execute(query, (gName, user, gDesc))
        conn.commit()
        query = 'INSERT INTO GroupMembership VALUES(%s, %s, %s)'
        cursor.execute(query, (user, gName, user))
        conn.commit()
        cursor.close()
        cursor2 = conn.cursor()
        query2 = 'SELECT gName, gCreator, gDesc FROM Group ORDER BY gName'
        cursor2.execute(query2)
        data2 = cursor2.fetchall()
        remind2 = "You have created this Group successfully!"
        return render_template('group.html', remind2=remind2, username=user, posts=data2)


# Reservation *** build after group and event
@app.route('/event')
def event():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT eID, eName, eDesc,eDate FROM Event ORDER BY eID DESC'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('event.html', username=user, posts=data)


@app.route('/createEvent', methods=['GET', 'POST'])
def createEvent():
    username = session['username']
    cursor = conn.cursor()
    query = 'Select gName From Group Where gCreator = %s'
    cursor.execute(query, (username))
    groupnames = cursor.fetchall()
    remind = None
    query = 'SELECT gCreator,gName FROM Group WHERE gCreator = %s'
    cursor.execute(query, (username))
    userinfo = cursor.fetchone()
    error1 = None

    if (userinfo):
        if request.method == "POST":
            eName = request.form['eName']
            eDesc = request.form.get('eDesc')
            eDate = request.form.get('eDate')
            gName = request.form.get('gName')
            query = 'INSERT INTO Event (eName, eDesc, eDate, gName, gCreator) VALUES(%s, %s, %s, %s, %s)'
            cursor.execute(query, (eName, eDesc, eDate, gName, username))
            conn.commit()
            query = 'select * from Event where eID = (select max(eID) from Event)'
            cursor.execute(query)
            for row in cursor:
                eID = row['eID']
                eName = row['eName']
                username = row['gCreator']
            cursor.close()
            remind = "You have created this Event successfully!"
        return render_template('createEvent.html', username=username, groupnames=groupnames, remind=remind)
    else:
        error1 = "You don't have this access!"
        return render_template('createEvent.html', error1=error1, username=username)


# Reservation *** build after group and event
@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    user = session['username']
    responses = ['Y', 'N']
    remind = None
    cursor = conn.cursor()
    query = 'SELECT eID, eName, eDesc,eDate FROM Event ORDER BY eID DESC'
    cursor.execute(query)
    conn.commit()
    data = cursor.fetchall()

    query = 'SELECT Event.eID, eName, eDesc,eDate,response FROM Event join RSVP On Event.eID = RSVP.eID Where username = %s'
    cursor.execute(query, (user))
    conn.commit()
    rsvps = cursor.fetchall()
    error2 = None

    if request.method == "POST":
        eID = request.form['eID']
        response = request.form.get('response')
        # check if has record user's response
        # repeat
        query = 'SELECT eID, username FROM RSVP WHERE username = %s and eID = %s and response = %s'
        cursor.execute(query, (user, eID, response))
        conn.commit()
        repeat = cursor.fetchall()
        # user history response for change
        query = 'SELECT eID, username FROM RSVP WHERE username = %s and eID = %s'
        cursor.execute(query, (user, eID))
        conn.commit()
        userinfo = cursor.fetchall()

        if(repeat):
            error2 = "Repeated request!"
            return render_template('rsvp.html', username=user, posts=data, responses=responses, error2=error2, remind=remind, rsvps=rsvps)
        # # record users response
        # first check if is an update request
        else:
            if (userinfo):
                query = 'Update RSVP SET response = %s Where username = %s and eID = %s'
                cursor.execute(query, (response, user, eID))
                conn.commit()
                cursor.close()
                remind = "You have change your mind successfully!"

                cursor1 = conn.cursor()
                query = 'SELECT Event.eID, eName, eDesc,eDate,response FROM Event join RSVP On Event.eID = RSVP.eID Where username = %s'
                cursor1.execute(query, (user))
                rsvps = cursor1.fetchall()
                return render_template('rsvp.html', username=user, posts=data, responses=responses, error2=error2, remind=remind, rsvps=rsvps)
            else:
                query = 'INSERT INTO RSVP VALUES(%s, %s, %s)'
                cursor.execute(query, (user, eID, response))
                conn.commit()
                cursor.close()
                remind = "You have attended this Event successfully!"

                cursor1 = conn.cursor()
                query = 'SELECT Event.eID, eName, eDesc,eDate,response FROM Event join RSVP On Event.eID = RSVP.eID Where username = %s'
                cursor1.execute(query, (user))
                rsvps = cursor1.fetchall()

    return render_template('rsvp.html', username=user, posts=data, responses=responses, error2=error2, remind=remind, rsvps=rsvps)


###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############
###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############
###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############
###### Wz ################### Wz ################### Wz ################### Wz ################### Wz #############

app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
