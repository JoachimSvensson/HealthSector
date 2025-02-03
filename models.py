from app import db

class Bemanningsplan(db.Model):
    __tablename__ = 'bemanningsplan'

    bid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Start = db.Column(db.String, nullable=False)
    End = db.Column(db.String, nullable=False)
    Monday = db.Column(db.Integer, nullable=False)
    Tuesday = db.Column(db.Integer, nullable=False)
    Wednesday = db.Column(db.Integer, nullable=False)
    Thursday = db.Column(db.Integer, nullable=False)
    Friday = db.Column(db.Integer, nullable=False)
    Saturday = db.Column(db.Integer, nullable=False)
    Sunday = db.Column(db.Integer, nullable=False)
    Week = db.Column(db.String, nullable=False)
    Navn = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"bemanningsplan med start kl {self.Start} og slutt kl {self.End} er registrert"
    

class PPP(db.Model):
    __tablename__ = 'ppp'
    
    pppid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Start = db.Column(db.String, nullable=False)
    End = db.Column(db.String, nullable=False)
    ppp_mon = db.Column(db.Integer, nullable=False)
    ppp_tue = db.Column(db.Integer, nullable=False)
    ppp_wed = db.Column(db.Integer, nullable=False)
    ppp_thu = db.Column(db.Integer, nullable=False)
    ppp_fri = db.Column(db.Integer, nullable=False)
    ppp_sat = db.Column(db.Integer, nullable=False)
    ppp_sun = db.Column(db.Integer, nullable=False)
    Week = db.Column(db.String, nullable=False)
    Navn = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"ppp oppsett for bemanningsplan med start kl {self.Start} og slutt kl {self.End} er registrert"
    

class Døgnrytmetabell(db.Model):
    __tablename__ = 'døgnrytmeplan'
    did = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Start = db.Column(db.String, nullable=False)
    End = db.Column(db.String, nullable=False)
    Aktivitet = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"døgnrytmeaktivitet er oppdatert og registrert for de ulike tidspunktene av døgnet"
    


class SykehusData(db.Model):
    __tablename__ = 'sykehusdata'
    sid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    År = db.Column(db.Integer, nullable=False)
    Måned = db.Column(db.String, nullable=False)
    Uke = db.Column(db.Integer, nullable=False)
    Dag = db.Column(db.String, nullable=False)
    DatoTid = db.Column(db.String, nullable=False) # evt bytte til DateTime, men da også endre i datalasten
    Timer = db.Column(db.Integer, nullable=False)
    post = db.Column(db.String, nullable=False)
    helg = db.Column(db.Integer, nullable=False)
    Antall_inn_på_post = db.Column(db.Float, nullable=True)
    Antall_pasienter_ut_av_Post = db.Column(db.Float, nullable=True)
    skift_type = db.Column(db.String, nullable=False)
    Belegg = db.Column(db.Float, nullable=True)
    Prediksjoner_pasientstrøm = db.Column(db.Float, nullable=True)
    Prediksjoner_belegg = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'sykehusdata er oppdatert og registrert i databasen'

    