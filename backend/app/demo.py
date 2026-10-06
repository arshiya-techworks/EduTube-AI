VIDEOS = [
 {"id": "rfscVS0vtbw", "title": "Learn Python - Full Course for Beginners", "channel": "freeCodeCamp.org", "duration": "4:26:52", "views": "40M views", "difficulty": "Beginner"},
 {"id": "kqtD5dpn9C8", "title": "Python for Beginners - Programming with Mosh", "channel": "Programming with Mosh", "duration": "1:00:00", "views": "20M views", "difficulty": "Beginner"},
 {"id": "HXV3zeQKqGY", "title": "SQL Tutorial - Full Database Course for Beginners", "channel": "freeCodeCamp.org", "duration": "4:20:00", "views": "15M views", "difficulty": "Beginner"},
 {"id": "i_LwzRVP7bg", "title": "Machine Learning for Everybody - Full Course", "channel": "freeCodeCamp.org", "duration": "3:53:00", "views": "5M views", "difficulty": "Intermediate"},
]
for v in VIDEOS: v["thumbnail"] = f"https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg"
# Short sample transcripts (demo content, topic-tagged sections).
PY = [
 ("Function basics", "A function is a reusable block of code defined with the def keyword. Functions help you avoid repeating code and make programs easier to read."),
 ("Parameters", "A parameter is a variable listed inside the parentheses of a function definition. An argument is the actual value you pass when calling the function."),
 ("Return statements", "The return statement sends a value back to the caller and ends the function. A function without return gives back None."),
 ("Default arguments", "Default arguments give a parameter a fallback value, for example def greet(name='friend'). Callers may then omit that argument."),
]
SQL = [
 ("Databases", "A relational database stores data in tables made of rows and columns. SQL is the language used to query and manage that data."),
 ("SELECT queries", "The SELECT statement retrieves columns from a table. The WHERE clause filters rows that match a condition."),
 ("Joins", "A JOIN combines rows from two tables using a related column. An INNER JOIN keeps only rows that match in both tables."),
 ("Aggregation", "Aggregate functions such as COUNT, SUM and AVG summarise many rows. GROUP BY splits rows into groups before aggregating."),
]
ML = [
 ("Supervised learning", "Supervised learning trains a model on labelled examples so it can predict labels for new data."),
 ("Features and labels", "Features are the input variables describing each sample. The label is the target value the model should predict."),
 ("Overfitting", "Overfitting happens when a model memorises training data and performs poorly on unseen data. Validation sets help detect it."),
 ("Evaluation", "Accuracy, precision and recall measure model quality. Choose the metric that matches the cost of mistakes."),
]
TRANSCRIPTS = {"rfscVS0vtbw": PY, "kqtD5dpn9C8": PY, "HXV3zeQKqGY": SQL, "i_LwzRVP7bg": ML}
def search(q):
    ql = q.lower().split()
    hits = [v for v in VIDEOS if not ql or any(w in (v["title"] + v["channel"]).lower() or w in " ".join(t for _, t in TRANSCRIPTS[v["id"]]).lower() for w in ql)]
    return hits or VIDEOS
