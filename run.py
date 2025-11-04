from app import create_app,db

app= create_app()

if __name__ == '__main__': 
    db.metadata.clear()
    app.run(debug=True)