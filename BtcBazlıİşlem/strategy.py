import ccxt, config
import pandas as pd
from smtplib import SMTP
import winsound
duration = 1000  # milliseconds
freq = 440  # Hz

islemGerceklesti = False
zamanAraligi = "1m"
symbol = input("İşlem Yapılacak Sembol (ETH, LTC, ADA...vb): ").upper()
symbolName = symbol + "/USDT"
price = input("İşlem Yapılacak BTC Fiyatı: ")
positionType = input("Fiyata Dokununca(1), Barı Fiyatın Üzerinde - Altında Kapatınca(2): ")
if float(positionType) < 1 or float(positionType) > 2:
    print("HATA! 1 veya 2 Dışında Bir Tuşa Bastınız...")
if float(positionType) == 2:
    zamanAraligi = input("Hangi Periyotluk Bar Kapanışında İşlem Gerçekleşsin (1m, 3m, 5m, 15m, 30m, 45m, 1h, 2h, 4h, 6h, 8h, 12h, 1d): ").lower()
position = input("Long Enter(1), Long Exit(2), Short Enter(3), Short Exit(4): ")
if float(position) < 1 or float(position) > 4:
    print("HATA! 1,2,3 veya 4 Dışında Bir Tuşa Bastınız...")
if float(position) == 1 or float(position) == 3:
    positionUsdt = input("Pozisyona kaç USDT ile gireceksiniz (100, 250, 1500... vb): ")
    if float(positionUsdt) <= 0:
        print("HATA! Geçersiz Miktar Girdiniz...")
    leverage = input ("Kaldıraç Büyüklüğü (Binance Vadeli İşlemlerde Aynı Kaldıracı Seçmeyi Unutmayın!): ")
    if float(leverage) < 1 or float(leverage) > 125:
        print("HATA! Geçersiz Miktar Girdiniz...")

# API CONNECT
exchange = ccxt.binance({
"apiKey": config.apiKey,
"secret": config.secretKey,

'options': {
'defaultType': 'future'
},
'enableRateLimit': True
})

while True:
    try:
        
        balance = exchange.fetch_balance()
        free_balance = exchange.fetch_free_balance()
        positions = balance['info']['positions']
        newSymbol = symbol+"USDT"
        current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == newSymbol]
        position_bilgi = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
        
        # LOAD BARS
        bars = exchange.fetch_ohlcv("BTC/USDT", timeframe=zamanAraligi, since = None, limit = 2)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        # LOAD BARS2
        bars2 = exchange.fetch_ohlcv("BTC/USDT", timeframe="1m", since = None, limit = 2)
        df2 = pd.DataFrame(bars2, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        # LOAD BARS3
        bars3 = exchange.fetch_ohlcv(symbolName, timeframe="1m", since = None, limit = 2)
        df3 = pd.DataFrame(bars3, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        #Pozisyonda olup olmadığını kontrol etme
        if not position_bilgi.empty and position_bilgi["positionAmt"][len(position_bilgi.index) - 1] != 0:
            pozisyondami = True
        else: 
            pozisyondami = False
            longPozisyonda = False
            shortPozisyonda = False
        
        # Long pozisyonda mı?
        if pozisyondami and float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) > 0:
            longPozisyonda = True
            shortPozisyonda = False
        # Short pozisyonda mı?
        if pozisyondami and float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) < 0:
            shortPozisyonda = True
            longPozisyonda = False
        
        if float(balance['total']["USDT"]) < float(positionUsdt) and (float(position) == 1 or float(position) == 3):
            print ("HATA! Hesabınızdaki USDT miktarı ", float(balance['total']["USDT"]), " fakat ", positionUsdt, " USDT ile işlem yapmak istiyorsunuz.")
        
        alinacak_miktar = (float(positionUsdt) * float(leverage)) / float(df3["close"][len(df.index) - 1])
        
        
        if (float(position) == 2 and longPozisyonda == False) or (float(position) == 4 and shortPozisyonda == False):
            print("HATA! Şuanda ", symbol, " ile açılmış bir işlem yok...")
            break
        
        else:
            
            # LONG ENTER
            def longEnter(alinacak_miktar):
                order = exchange.create_market_buy_order(symbolName, alinacak_miktar)
                winsound.Beep(freq, duration)
                baslik = symbolName
                message = "LONG ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))

            # LONG EXIT
            def longExit():
                order = exchange.create_market_sell_order(symbolName, float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]), {"reduceOnly": True})
                winsound.Beep(freq, duration)
                baslik = symbolName
                message = "LONG EXIT\n" + "Toplam Para: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))

            # SHORT ENTER
            def shortEnter(alincak_miktar):
                order = exchange.create_market_sell_order(symbolName, alincak_miktar)
                winsound.Beep(freq, duration)
                baslik = symbolName
                message = "SHORT ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
            
            # SHORT EXIT
            def shortExit():
                order = exchange.create_market_buy_order(symbolName, (float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) * -1) , {"reduceOnly": True})
                winsound.Beep(freq, duration)
                baslik = symbolName
                message = "SHORT EXIT\n" + "Toplam Para: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
            
             # Fiyata dokunma
            
            if float(positionType) == 1 and islemGerceklesti == False:
                # Fiyata dokununca long enter
                if float(position) == 1 and float(df2["high"][len(df.index) - 1]) >= float(price):
                    longEnter(alinacak_miktar)
                    islemGerceklesti = True
                # fiyata dokununca long exit
                if float(position) == 2 and float(df2["low"][len(df.index) - 1]) <= float(price):
                    longExit()
                    islemGerceklesti = True
                # fiyata dokununca short enter
                if float(position) == 3 and float(df2["low"][len(df.index) - 1]) <= float(price):
                    shortEnter(alinacak_miktar)
                    islemGerceklesti = True
                # fiyata dokununca short exit
                if float(position) == 4 and float(df2["high"][len(df.index) - 1]) >= float(price):
                    shortExit()
                    islemGerceklesti = True
                
            # Bar kapatma
            if float(positionType) == 2 and islemGerceklesti == False:
                # fiyatın üzerinde bar kapatınca long enter
                if float(position) == 1 and float(df["close"][len(df.index) - 2]) >= float(price):
                    longEnter(alinacak_miktar)
                    islemGerceklesti = True
                # fiyatın altında bar kapatınca long exit
                if float(position) == 2 and float(df["close"][len(df.index) - 2]) <= float(price):
                    longExit()
                    islemGerceklesti = True
                # fiyatın altında bar kapatınca short enter
                if float(position) == 3 and float(df["close"][len(df.index) - 2]) <= float(price):
                    shortEnter(alinacak_miktar)
                    islemGerceklesti = True
                # fiyatın üzerinde bar kapatınca short exit
                if float(position) == 4 and float(df["close"][len(df.index) - 2]) >= float(price):
                    shortExit()
                    islemGerceklesti = True
                           
            
            if islemGerceklesti == False:
                print("============================== BİLGİLER ==============================")
                print("BTC anlık fiyatı: ", float(df2["high"][len(df.index) - 1]))
                print("Kaldıraç: ", leverage)
                print("Toplam USDT: ", float(balance['total']["USDT"]))
                if float(positionType) == 1:
                    print("BTC eğer ", price, " fiyatına değerse,")
                    if float(position) == 1:
                        print(float(positionUsdt), " USDT'lik ", symbol, " Long pozisyonu açılacak.")
                    if float(position) == 2:
                        print(symbol, " Long pozisyonunuz kapatılacak.")
                    if float(position) == 3:
                        print(float(positionUsdt), " USDT'lik ", symbol, " Short pozisyonu açılacak.")
                    if float(position) == 4:
                        print(symbol, " Short pozisyonunuz kapatılacak.")
                        
                if float(positionType) == 2:
                    if float(position) == 1:
                        print("BTC eğer ", price, " fiyatının üzerinde ", zamanAraligi+"'lik bar kapanırsa,")
                        print(float(positionUsdt), " USDT'lik ", symbol, " Long pozisyonu açılacak.")
                    if float(position) == 2:
                        print("BTC eğer ", price, " fiyatının altında ", zamanAraligi+"'lik bar kapanırsa,")
                        print(symbol, " Long pozisyonunuz kapatılacak.")
                    if float(position) == 3:
                        print("BTC eğer ", price, " fiyatının altında ", zamanAraligi+"'lik bar kapanırsa,")
                        print(float(positionUsdt), " USDT'lik ", symbol, " Short pozisyonu açılacak.")
                    if float(position) == 4:
                        print("BTC eğer ", price, " fiyatının üzerinde ", zamanAraligi+"'lik bar kapanırsa,")
                        print(symbol, " Short pozisyonunuz kapatılacak.")
            
            if islemGerceklesti == True:
                break
                    
    except ccxt.BaseError as Error:
        print ("[ERROR] ", Error )
        continue