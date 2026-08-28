from Flask import Flask
app=Flask(___name___)
@app.route("/")
def home():
  return "campus complaint Tracker is working!"
if ___name___=="___main___":
  app.run(debug=True)
