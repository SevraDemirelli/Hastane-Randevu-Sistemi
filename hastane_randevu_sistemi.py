import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class Hasta:
    def __init__(self, isim, tc):
        self.isim = isim
        self.tc = tc
        self.randevular = []

    def randevu_al(self, randevu):
        self.randevular.append(randevu)

    def randevu_iptal(self, randevu):
        self.randevular.remove(randevu)

class Doktor:
    def __init__(self, isim, uzmanlık, calisma_saatleri):
        self.isim = isim
        self.uzmanlık = uzmanlık
        self.calisma_saatleri = calisma_saatleri
        self.müsaitlik = True

class Randevu:
    def __init__(self, tarih, doktor, hasta):
        self.tarih = tarih
        self.doktor = doktor
        self.hasta = hasta

class RandevuSistemiGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Hastane Randevu Sistemi")
        self.root.geometry("400x500")
        self.kilavuz_buton = tk.Button(self.giris_pencere_olustur(), text="Kullanıcı Kılavuzu", command=self.kullanici_kilavuzu_ac, width=15 ,background="grey", relief="flat"
                                       , pady=2, font=("Arial", 8))
        self.kilavuz_buton.pack(pady=0, ipady=0, side="bottom", anchor="ne")

        self.tarih_secim = None  # tarih_secim özniteliğini tanımla

        self.conn = sqlite3.connect('randevular.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS doktorlar (
                                    isim TEXT NOT NULL,
                                    uzmanlık TEXT NOT NULL,
                                    calisma_saatleri TEXT NOT NULL,
                                    musaitlik INTEGER NOT NULL,  -- 1: Müsait, 0: Müsait Değil
                                    PRIMARY KEY (isim)
                                  )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS randevular (
                                tarih TEXT NOT NULL,
                                doktor TEXT NOT NULL,
                                hasta TEXT NOT NULL,
                                FOREIGN KEY (doktor) REFERENCES doktorlar(isim),
                                FOREIGN KEY (hasta) REFERENCES hastalar(isim)
                              )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS hastalar (
	                        isim	TEXT NOT NULL,
	                        tc	INTEGER NOT NULL,
	                        PRIMARY KEY(isim)
                            )''')

        self.conn.commit()

        self.hastalar = []
        self.doktorlar = []

    def kullanici_kilavuzu_ac(self):
            kilavuz_metni = """
            Kullanıcı Kılavuzu:
            1. Randevu Al butonuna tıklayarak randevu alabilirsiniz.
            2. Randevu İptal butonuna tıklayarak var olan bir randevunuzu iptal edebilirsiniz.
            3. Randevularımı Görüntüle butonuna tıklayarak mevcut randevularınızı listeleyebilirsiniz.
            4. Müsaitlik Durumu butonuna tıklayarak doktorların müsaitlik durumlarını görebilirsiniz.
            5. Profilimi Güncelle butonuna tıklayarak kullanıcı bilgilerinizi güncelleyebilirsiniz.
            """
            messagebox.showinfo("Kullanıcı Kılavuzu", kilavuz_metni)

    def hasta_giris(self):
        isim = self.isim_entry.get()
        tc = self.tc_entry.get()

        if not isim or not tc:
            self.hata_mesaji("Lütfen tüm alanları doldurun.")
            return

        # Hasta bilgilerini veritabanından kontrol et
        self.cursor.execute("SELECT * FROM hastalar WHERE isim=? AND tc=?", (isim, tc))
        hasta_verileri = self.cursor.fetchone()

        if hasta_verileri:
            self.giris_pencere.destroy()
            # Hasta objesini oluştur
            self.hasta = Hasta(hasta_verileri[0], hasta_verileri[1])
            self.baslangic_penceresi()
        else:
            self.hata_mesaji("Kullanıcı bulunamadı. Lütfen kayıt olun.")

    def hasta_kayit(self):
        isim = self.isim_entry.get()
        tc = self.tc_entry.get()

        if not isim or not tc:
            self.hata_mesaji("Lütfen tüm alanları doldurun.")
            return
        if len(tc) != 11:
            self.hata_mesaji("TC Kimlik Numarası 11 karakter olmalıdır.")
            return
        self.hasta = Hasta(isim, tc)
        self.hastalar.append(self.hasta)

        try:
            self.cursor.execute("INSERT INTO hastalar (isim, tc) VALUES (?, ?)", (isim, int(tc)))
            self.conn.commit()
        except sqlite3.Error as e:
            self.hata_mesaji("Veritabanı hatası: " + str(e))
            self.conn.commit()

        self.basarili_mesaji("Hesabınız başarıyla oluşturuldu. Lütfen giriş yapın.")

    def veritabanindan_doktorlari_al(self):
        self.cursor.execute("SELECT isim, uzmanlık, calisma_saatleri FROM doktorlar")
        doktorlar = self.cursor.fetchall()

        self.doktorlar = []  # Doktor nesnelerini saklamak için boş bir liste oluştur

        for doktor in doktorlar:
            doktor_objesi = Doktor(doktor[0], doktor[1], doktor[2])  # Doktor nesnesini oluştur
            self.doktorlar.append(doktor_objesi)  # Oluşturulan doktor nesnesini listeye ekle

        # Doktor isimlerini ve çalışma saatlerini ayrı ayrı listelerde saklamak için
        doktor_isimleri = [doktor.isim for doktor in self.doktorlar]
        calisma_saatleri = [saat for doktor in self.doktorlar for saat in doktor.calisma_saatleri.split(",")]

        self.doktor_secim["values"] = doktor_isimleri
        self.tarih_secim["values"] = calisma_saatleri

    def veritabanindan_randevulari_al(self):
        self.cursor.execute("SELECT tarih, doktor, hasta FROM randevular")
        randevular = self.cursor.fetchall()

        self.hastalar = []  # Hasta nesnelerini saklamak için boş bir liste oluştur
        self.doktorlar = []  # Doktor nesnelerini saklamak için boş bir liste oluştur
        self.randevular = []  # Randevu nesnelerini saklamak için boş bir liste oluştur

        for randevu in randevular:
            tarih = randevu[0]
            doktor_isim = randevu[1]
            hasta_isim = randevu[2]

            doktor = self.doktor_bul(doktor_isim)
            hasta = self.hasta_bul(hasta_isim)

            if doktor and hasta:
                randevu_objesi = Randevu(tarih, doktor, hasta)
                self.randevular.append(randevu_objesi)
            else:
                print(f"Hata: Randevu oluşturulamadı - Doktor: {doktor_isim}, Hasta: {hasta_isim}")

    def hasta_bul(self, isim, tc):
        for hasta in self.hastalar:
            if hasta.isim == isim and hasta.tc == tc:
                return hasta
        return None

    def doktor_bul(self, isim):
        for doktor in self.doktorlar:
            if doktor.isim == isim:
                return doktor
        return None

    def baslangic_penceresi(self):
        self.baslangic_pencere = tk.Frame(self.root)
        self.baslangic_pencere.place(relx=0.5, rely=0.5 , anchor="center")

        baslik = tk.Label(self.baslangic_pencere, text="Hastane Randevu Sistemi", font=("Arial", 14, "bold italic"))
        baslik.pack(pady=20)

        butonlar_frame = tk.Frame(self.baslangic_pencere)
        butonlar_frame.pack(pady=4, padx=1, fill="both")

        butonlar = [
            ("Randevu Al", self.randevu_al_pencere_olustur),
            ("Randevu İptal", self.randevu_iptal_pencere_olustur),
            ("Randevularımı Görüntüle", self.randevularimi_goruntule),
            ("Müsaitlik Durumu", self.musaitlik_durumu_pencere),
            ("Profilimi Güncelle", self.profil_guncelle_pencere_olustur)
        ]

        for text, command in butonlar:
            buton = tk.Button(butonlar_frame, text=text, command=command,width=23, bg="#2196F3", background="light grey", relief="flat", pady=1, font=("Arial", 10))
            buton.pack(pady=5, ipady=5)

    def randevu_al_pencere_olustur(self):
        self.randevu_al_pencere = tk.Toplevel(self.root)
        self.randevu_al_pencere.title("Randevu Al")
        self.randevu_al_pencere.geometry("400x200")
        baslik = tk.Label(self.randevu_al_pencere, text="Randevu Al", font=("Arial", 14, "bold"))
        baslik.pack(pady=10)

        frame = tk.Frame(self.randevu_al_pencere)
        frame.pack(pady=10, padx=20)
        tk.Label(frame, text="Doktor Seçiniz:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.doktor_secim = ttk.Combobox(frame, values=[doktor.isim for doktor in self.doktorlar], width=25)
        self.doktor_secim.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.doktor_secim.bind("<<ComboboxSelected>>", self.guncel_saatleri_getir)




        self.randevu_al_pencere.grid_columnconfigure(1, weight=1)





        tk.Label(frame, text="Randevu Saati Seçiniz:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5,
                                                                                sticky="w")
        self.tarih_secim = ttk.Combobox(frame, width=25)
        self.tarih_secim.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        randevu_al_buton = tk.Button(self.randevu_al_pencere, text="Randevu Al", command=self.randevu_olustur, width=15,
                                     bg="#2196F3", background="light grey", relief="flat", pady=1, font=("Arial", 10))
        randevu_al_buton.pack(pady=20, ipady=5)
        self.veritabanindan_doktorlari_al()
    def guncel_saatleri_getir(self, event=None):
        secili_doktor_isim = self.doktor_secim.get()
        if not secili_doktor_isim:
            return

        secili_doktor = None
        for doktor in self.doktorlar:
            if doktor.isim == secili_doktor_isim:
                secili_doktor = doktor
                break

        if not secili_doktor:
            return

        calisma_saatleri = secili_doktor.calisma_saatleri.split(",") if secili_doktor.calisma_saatleri else []

        saat_secenekleri = []
        for saat in calisma_saatleri:
            saat_secenekleri.extend([f"{saat}:00", f"{saat}:30"])

        self.tarih_secim["values"] = saat_secenekleri
    def randevu_olustur(self):
        doktor_isim = self.doktor_secim.get()
        tarih = self.tarih_secim.get()

        if not doktor_isim or not tarih:
            self.hata_mesaji("Lütfen tüm alanları doldurun.")
            return

        doktor = self.doktor_bul(doktor_isim)
        if not doktor:
            self.hata_mesaji("Geçerli bir doktor seçiniz.")
            return

        randevu = Randevu(tarih, doktor, self.hasta)
        self.hasta.randevu_al(randevu)

        self.cursor.execute("INSERT INTO randevular (tarih, doktor, hasta) VALUES (?, ?, ?)", (tarih, doktor_isim, self.hasta.isim))
        self.conn.commit()

        self.basarili_mesaji("Randevu başarıyla oluşturuldu.")
        self.randevu_al_pencere.destroy()

    def randevu_iptal_pencere_olustur(self):
        self.randevu_iptal_pencere = tk.Toplevel(self.root)
        self.randevu_iptal_pencere.title("Randevu İptal")
        self.randevu_iptal_pencere.geometry("300x300")

        self.randevu_iptal_pencere.grid_columnconfigure(0, weight=1)
        self.randevu_iptal_pencere.grid_rowconfigure(1, weight=1)

        baslik = tk.Label(self.randevu_iptal_pencere, text="Randevu İptal", font=("Arial", 14, "bold"))
        baslik.pack(pady=10)

        frame = tk.Frame(self.randevu_iptal_pencere)
        frame.pack(pady=10, padx=20)

        tk.Label(frame, text="Randevularınız:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.randevular_liste = tk.Listbox(frame, selectmode=tk.SINGLE, width=30, height=5)
        self.randevular_liste.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        for randevu in self.hasta.randevular:
            self.randevular_liste.insert(tk.END, f"{randevu.doktor.isim} - {randevu.tarih}")

        randevu_iptal_buton = tk.Button(self.randevu_iptal_pencere, text="Randevu İptal Et", command=self.randevu_iptal, width=15, bg="#2196F3", background="light grey", relief="flat", pady=1, font=("Arial", 10))
        randevu_iptal_buton.pack(pady=20, ipady=5)

    def randevu_iptal(self):
        secili_index = self.randevular_liste.curselection()

        if not secili_index:
            self.hata_mesaji("Lütfen bir randevu seçin.")
            return

        secili_randevu = self.hasta.randevular[secili_index[0]]
        self.hasta.randevu_iptal(secili_randevu)
        self.randevular_liste.delete(secili_index)

        self.cursor.execute("DELETE FROM randevular WHERE tarih=? AND doktor=? AND hasta=?", (secili_randevu.tarih, secili_randevu.doktor.isim, self.hasta.isim))
        self.conn.commit()

        self.basarili_mesaji("Randevu başarıyla iptal edildi.")
        self.randevu_iptal_pencere.destroy()

    def saatleri_goster(self, calisma_saatleri):
        saat_secenekleri = []

        for saat in calisma_saatleri:
            for dakika in [':00', ':30']:
                saat_secenekleri.append(f"{saat}{dakika}")

        return saat_secenekleri

    def musaitlik_durumu_pencere(self):
        self.musaitlik_durumu_pencere = tk.Toplevel(self.root)
        self.musaitlik_durumu_pencere.title("Müsaitlik Durumu")
        self.musaitlik_durumu_pencere.geometry("700x500")

        baslik = tk.Label(self.musaitlik_durumu_pencere, text="Müsaitlik Durumu", font=("Arial", 16, "bold"))
        baslik.pack(pady=20)

        # Frame oluştur
        frame = tk.Frame(self.musaitlik_durumu_pencere)
        frame.pack(pady=20, padx=10)
        # Doktor bilgilerini veritabanından çek
        conn = sqlite3.connect('randevular.db')
        cursor = conn.cursor()
        cursor.execute("SELECT isim, uzmanlık, calisma_saatleri, musaitlik FROM doktorlar")
        doktorlar = cursor.fetchall()

        # Her bir doktor için kart oluştur
        for doktor in doktorlar:
            kart = tk.Frame(frame, bg="white", padx=10, pady=10)
            kart.pack(pady=10, fill="x")

            # Doktor bilgilerini kart üzerinde göster
            tk.Label(kart, text="Doktor:", font=("Arial", 12, "bold italic")).grid(row=0, column=0, sticky="w")
            tk.Label(kart, text=doktor[0], font=("Arial", 12)).grid(row=0, column=1, sticky="w")

            tk.Label(kart, text="Uzmanlık Alanı:", font=("Arial", 12, "bold italic")).grid(row=1, column=0, sticky="w")
            tk.Label(kart, text=doktor[1], font=("Arial", 12)).grid(row=1, column=1, sticky="w")

            tk.Label(kart, text="Müsaitlik Durumu:", font=("Arial", 12, "bold italic")).grid(row=2, column=0,
                                                                                             sticky="w")
            durum = "Müsait" if doktor[3] == 1 else "Müsait Değil"
            tk.Label(kart, text=durum, font=("Arial", 12)).grid(row=2, column=1, sticky="w")

            tk.Label(kart, text="Çalışma Saatleri:", font=("Arial", 12, "bold italic")).grid(row=3, column=0,
                                                                                             sticky="w")

            # Çalışma saatlerini virgülle ayırarak listeye dönüştür
            calisma_saatleri = doktor[2].split(',')
            saatler = self.saatleri_goster(calisma_saatleri)
            saatler_metni = ", ".join(saatler)
            tk.Label(kart, text=saatler_metni, font=("Arial", 12)).grid(row=3, column=1, sticky="w")

        conn.close()

    def randevularimi_goruntule(self):
        self.randevular_pencere = tk.Toplevel(self.root)
        self.randevular_pencere.title("Randevularım")
        self.randevular_pencere.geometry("400x300")

        self.randevular_pencere.grid_columnconfigure(0, weight=1)
        self.randevular_pencere.grid_rowconfigure(1, weight=1)

        baslik = tk.Label(self.randevular_pencere, text="Randevularım", font=("Arial", 14, "bold"))
        baslik.pack(pady=10)

        frame = tk.Frame(self.randevular_pencere)
        frame.pack(pady=10, padx=20)

        self.randevular_liste = tk.Listbox(frame, selectmode=tk.SINGLE, width=40, height=10)
        self.randevular_liste.pack(pady=10)

        for randevu in self.hasta.randevular:
            self.randevular_liste.insert(tk.END, f"{randevu.doktor.isim} - {randevu.tarih}")

    def randevu_saatleri(self):
        saatler = []
        for saat in range(8, 18):
            saatler.append(f"{saat}:00")
            saatler.append(f"{saat}:30")
        return saatler

    def profil_guncelle_pencere_olustur(self):
        self.profil_guncelle_pencere = tk.Toplevel(self.root)
        self.profil_guncelle_pencere.title("Profilimi Güncelle")
        self.profil_guncelle_pencere.geometry("400x200")

        self.profil_guncelle_pencere.grid_columnconfigure(1, weight=1)

        baslik = tk.Label(self.profil_guncelle_pencere, text="Profilimi Güncelle", font=("Arial", 14, "bold"))
        baslik.pack(pady=10)

        frame = tk.Frame(self.profil_guncelle_pencere)
        frame.pack(pady=10, padx=20)

        tk.Label(frame, text="İsim:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.yeni_isim_entry = tk.Entry(frame)
        self.yeni_isim_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(frame, text="Yeni TC Kimlik No:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.yeni_tc_entry = tk.Entry(frame)
        self.yeni_tc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        guncelle_buton = tk.Button(self.profil_guncelle_pencere, text="Bilgilerimi Güncelle", command=self.profil_guncelle, width=15, bg="#2196F3", background="light grey", relief="flat", pady=1, font=("Arial", 10))
        guncelle_buton.pack(pady=10, ipady=5)

    def profil_guncelle(self):
        yeni_isim = self.yeni_isim_entry.get()
        yeni_tc = self.yeni_tc_entry.get()

        if not yeni_isim and not yeni_tc:
            self.hata_mesaji("Lütfen en az bir alanı doldurun.")
            return

        # Yeni isim veya TC girilmişse, ilgili alanları güncelle
        if yeni_isim:
            self.hasta.isim = yeni_isim
        if yeni_tc:
            # TC Kimlik No'nun 11 karakterden oluştuğunu ve sadece rakamlardan oluştuğunu kontrol et
            if not yeni_tc.isdigit() or len(yeni_tc) != 11:
                self.hata_mesaji(
                    "Geçersiz TC Kimlik Numarası. TC Kimlik Numarası 11 karakter olmalıdır ve yalnızca rakamlardan oluşmalıdır.")
                return
            self.hasta.tc = yeni_tc

        self.cursor.execute("UPDATE hastalar SET isim=?, tc=? WHERE isim=?",
                            (self.hasta.isim, self.hasta.tc, self.hasta.isim))
        self.conn.commit()

        self.basarili_mesaji("Bilgileriniz başarıyla güncellendi.")
        self.profil_guncelle_pencere.destroy()
    def cikis_yap(self):
        self.root.destroy()

    def hata_mesaji(self, mesaj):
        messagebox.showerror("Hata", mesaj)

    def basarili_mesaji(self, mesaj):
        messagebox.showinfo("Başarılı", mesaj)



    def giris_pencere_olustur(self):
        self.giris_pencere = tk.Frame(self.root)
        self.giris_pencere.pack(expand=True, )
        baslik = tk.Label(self.giris_pencere, text="Hasta Girişi", font=("Arial", 18, "bold"))
        baslik.pack(pady=10 )

        frame = tk.Frame(self.giris_pencere)
        frame.pack(pady=10)

        tk.Label(frame, text="İsim:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.isim_entry = tk.Entry(frame)
        self.isim_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(frame, text="TC Kimlik No:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tc_entry = tk.Entry(frame)
        self.tc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")


        giris_buton = tk.Button(self.giris_pencere, text="Giriş Yap", command=self.hasta_giris, width=15, bg="#4CAF50",
                                background="light grey", font=("Arial", 10))
        giris_buton.pack(side="left", padx=5)

        kayit_buton = tk.Button(self.giris_pencere, text="Kayıt Ol", command=self.hasta_kayit, width=15, bg="#2196F3",
                                background="light grey", font=("Arial", 10))
        kayit_buton.pack(side="left", padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = RandevuSistemiGUI(root)
    root.mainloop()
