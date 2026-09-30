import os,csv,random,pickle
from sklearn.ensemble import RandomForestClassifier
ROOT=os.path.dirname(os.path.dirname(__file__)); DATA=os.path.join(ROOT,'data','health_data.csv'); MODEL_PATH=os.path.join(ROOT,'model','risk_model.pkl'); F=['age','bmi','blood_pressure','glucose','activity_hours','sleep_hours']
def train_model(n=600):
 random.seed(42); rows=[]
 for _ in range(n):
  age=random.randint(18,80); bmi=round(random.uniform(17,36),1); bp=random.randint(90,170); g=random.randint(65,210); a=round(random.uniform(.2,12),1); s=round(random.uniform(4,9.5),1)
  z=max(0,age-45)*.035+max(0,bmi-25)*.08+max(0,bp-120)*.025+max(0,g-100)*.02-max(0,a-4)*.06+max(0,7-s)*.06+random.uniform(-.35,.35)
  label='Low' if z<1 else 'Moderate' if z<2 else 'High'; rows.append([age,bmi,bp,g,a,s,label])
 os.makedirs(os.path.dirname(DATA),exist_ok=True)
 with open(DATA,'w',newline='',encoding='utf8') as f: csv.writer(f).writerows([F+['risk_label']]+rows)
 m=RandomForestClassifier(n_estimators=120,max_depth=7,random_state=42).fit([r[:6] for r in rows],[r[6] for r in rows]); pickle.dump(m,open(MODEL_PATH,'wb')); return m
def load_model(): return pickle.load(open(MODEL_PATH,'rb')) if os.path.exists(MODEL_PATH) else train_model()
def predict_risk(v):
 m=load_model(); p=m.predict_proba([v])[0]; i=max(range(len(p)),key=lambda j:p[j]); return m.classes_[i],float(p[i])
if __name__=='__main__': train_model(); print('Synthetic data + model created.')
