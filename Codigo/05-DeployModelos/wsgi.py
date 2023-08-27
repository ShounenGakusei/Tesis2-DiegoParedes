from Deploy import app

if __name__ == "__main__":
    app.run(debug=False, threaded=False,host='0.0.0.0')