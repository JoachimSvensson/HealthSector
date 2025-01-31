from app import db

class Bemanningsplan(db.Model):
    __tablename__ = 'bemanningsplan'

    bid = db.Column(db.Integer, primary_key=True)
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
    
    pppid = db.Column(db.Integer, primary_key=True)
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
    did = db.Column(db.Integer, primary_key=True)
    Start = db.Column(db.String, nullable=False)
    End = db.Column(db.String, nullable=False)
    Aktivitet = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"døgnrytmeaktivitet er oppdatert og registrert for de ulike tidspunktene av døgnet"
    

    