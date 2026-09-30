from flask import Flask,render_template,request,redirect,url_for,session,flash
import sqlite3,hashlib,hmac,os,csv
from functools import wraps
from model.train_model import train_model,predict_risk,MODEL_PATH
app=Flask(__name__); app.secret_key=os.environ.get('SECUREAI_SECRET_KEY','demo-change-this-secret')
ROOT=os.path.dirname(__file__); DB=os.path.join(ROOT,'secureai.db'); DATA=os.path.join(ROOT,'data','health_data.csv')
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def hp(p,s=None):
 s=s or os.urandom(16); return s.hex()+':'+hashlib.pbkdf2_hmac('sha256',p.encode(),s,120000).hex()
def vp(p,x):
 try:
  s,k=x.split(':'); return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),120000).hex(),k)
 except: return False
def init():
 c=db(); c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password_hash TEXT,role TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY,username TEXT,age INTEGER,bmi REAL,bp REAL,glucose REAL,activity REAL,sleep REAL,label TEXT,prob REAL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
 if not c.execute('SELECT id FROM users WHERE username=?',('admin',)).fetchone(): c.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',('admin',hp('admin123'),'admin'))
 c.commit(); c.close()
def req(f):
 @wraps(f)
 def w(*a,**k): return f(*a,**k) if 'username' in session else redirect(url_for('login'))
 return w
def summary():
 d={'rows':0,'low':0,'moderate':0,'high':0}
 if os.path.exists(DATA):
  with open(DATA,encoding='utf8') as f:
   rows=list(csv.DictReader(f)); d['rows']=len(rows)
   for r in rows: d[r['risk_label'].lower()]+=1
 return d
@app.route('/')
def home(): return redirect(url_for('dashboard')) if 'username' in session else render_template('home.html')
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  u=request.form['username'].strip(); p=request.form['password']; c=db(); x=c.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone(); c.close()
  if x and vp(p,x['password_hash']): session['username']=u; session['role']=x['role']; return redirect(url_for('dashboard'))
  flash('Invalid username or password.','error')
 return render_template('login.html')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))
@app.route('/dashboard')
@req
def dashboard():
 c=db(); hist=c.execute('SELECT * FROM predictions ORDER BY id DESC LIMIT 10').fetchall(); total=c.execute('SELECT COUNT(*) c FROM predictions').fetchone()['c']; c.close(); return render_template('dashboard.html',history=hist,total=total,summary=summary())
@app.route('/predict',methods=['POST'])
@req
def predict():
 try:
  v=[float(request.form[x]) for x in ['age','bmi','bp','glucose','activity','sleep']]
  if not 10<=v[0]<=100 or any(x<0 for x in v[1:]): raise ValueError('Enter non-negative values and age 10-100.')
  label,prob=predict_risk(v); c=db(); c.execute('INSERT INTO predictions(username,age,bmi,bp,glucose,activity,sleep,label,prob) VALUES(?,?,?,?,?,?,?,?,?)',(session['username'],*v,label,prob)); c.commit(); c.close(); return render_template('result.html',label=label,prob=round(prob*100,2),values=v)
 except Exception as e: flash('Input error: '+str(e),'error'); return redirect(url_for('dashboard'))
@app.route('/data')
@req
def data():
 rows=[]
 if os.path.exists(DATA):
  with open(DATA,encoding='utf8') as f: rows=list(csv.DictReader(f))[:100]
 return render_template('data.html',rows=rows)
if __name__=='__main__':
 init()
 if not os.path.exists(MODEL_PATH): train_model()
 print('Open http://127.0.0.1:5000 | demo: admin / admin123'); app.run(host='0.0.0.0',port=8080,debug=False)
