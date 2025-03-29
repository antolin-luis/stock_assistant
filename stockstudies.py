# %%


# %% [markdown]
# ## Coletando ticks por setor da B3

# %%
from pathlib import Path
from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from sqlalchemy import create_engine
import os

# %%
download_path = "/home/luisantolin/"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("start-maximized")
options.add_argument("--window-size=1920x1080")
options.add_argument("--disable-notifications")
options.add_argument("--no-sandbox")
options.add_argument("--verbose")
prefs = {
    "download.default_directory": download_path,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing_for_trusted_sources_enabled": False,
    "safebrowsing.enabled": False,
}
options.add_experimental_option("prefs", prefs)

# driver = webdriver.Chrome(options=options)


# %%
def get_ticks_by_sector():
    with webdriver.Chrome(options=options) as driver:
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        url = (
            "https://sistemaswebb3-listados.b3.com.br/indexPage/day/IBRA?language=pt-br"
        )
        driver.get(url)
        sleep(2)
        driver.find_element(By.ID, "segment").send_keys("Setor de Atuação")
        sleep(1)
        driver.find_element(
            By.XPATH,
            "/html/body/app-root/app-day-portfolio/div/div/div[1]/form/div[2]/div/div[2]/div/div/div[1]/div[2]/p/a",
        ).click()
        sleep(1)

    for p in Path(download_path).glob("IBRADia*"):
        ticks = pd.read_csv(
            str(p),
            sep=";",
            encoding="ISO-8859-1",
            skipfooter=2,
            engine="python",
            thousands=".",
            decimal=",",
            header=1,
            index_col=False,
        )
        p.unlink()

    return ticks


# %%
df = get_ticks_by_sector()

# %%
df = df.rename(
    columns={
        "Setor": "sector",
        "Código": "tick",
        "Ação": "stock_name",
        "Tipo": "class_type",
        "Qtde. Teórica": "volume",
        "Part. (%)": "share_prc",
        "Part. (%)Acum.": "acumm_share_prc",
    }
)

# %%
df["sector"] = [i.split(" / ")[1] if " / " in i else i for i in df.sector]
df["sector"] = [i.split("/")[1] if "/" in i else i for i in df.sector]

# %%
df["sector_id"] = df.groupby("sector").ngroup()

df.to_csv(os.path.join(download_path,'code/stock-services'),index=False)

# %%

# Lembrar de descomentar essa parte para usar no raspbery
# engine = create_engine(
#     "postgresql://luis-antolin:Agro_antol_2503@localhost:5432/stocks_db",
#     connect_args={"options": "-csearch_path={}".format("stock_studies")},
# )
#

#Lembrar de descomentar essa parte para usar no db local
# engine = create_engine(
#     "postgresql://luis-antolin:Agro_antol_2503@192.168.0.232:5432/stocks_db",
#     connect_args={"options": "-csearch_path={}".format("stock_studies")},
# )

# %%
#df.to_sql("sector_table", engine, schema="public", if_exists="replace", index=False)


### parte experimental


# import fundamentus
# import pandas as pd
# import matplotlib.pyplot as plt
#
# # %%
# df = fundamentus.get_resultado()
#
# # %%
# df.head()
#
# # %%
# df.loc[["BBAS3"]]
#
# # %% [markdown]
# # ## Usando selenium para extrair do status invest
#
# # %% [markdown]
# # ### Cotações do mercado brasileiro
# # %%
# from selenium import webdriver
# from time import sleep
# from selenium.webdriver.common.by import By
# import pandas as pd
# from selenium_stealth import stealth
# import glob
# import os
# from pathlib import Path
#
# # %%
# URL = "https://statusinvest.com.br/acoes/busca-avancada"
# download_path = "/home/luis-antolin/stocks/files/statusinvest_br"
#
# for p in Path(download_path).glob("statusinvest-busca-avancada*"):
#     p.unlink()
#
#
# options = webdriver.ChromeOptions()
# options.add_argument("--headless")
# options.add_argument("start-maximized")
# options.add_argument("--window-size=1920x1080")
# options.add_argument("--disable-notifications")
# options.add_argument("--no-sandbox")
# options.add_argument("--verbose")
# prefs = {
#     "download.default_directory": download_path,
#     "download.prompt_for_download": False,
#     "download.directory_upgrade": True,
#     "safebrowsing_for_trusted_sources_enabled": False,
#     "safebrowsing.enabled": False,
# }
#
# options.add_experimental_option("prefs", prefs)
#
# with webdriver.Chrome(options=options) as driver:
#     stealth(
#         driver,
#         languages=["en-US", "en"],
#         vendor="Google Inc.",
#         platform="Win32",
#         webgl_vendor="Intel Inc.",
#         renderer="Intel Iris OpenGL Engine",
#         fix_hairline=True,
#     )
#     # driver = webdriver.Chrome(options=options)
#     driver.get(URL)
#     # driver.get_screenshot_as_file('/home/me/stocks/files/statusinvest_br/see.png')
#     button_buscar = driver.find_element(
#         By.XPATH, '//*[@id="main-2"]/div[3]/div/div/div/button[2]'
#     ).click()
#     sleep(3)
#     button_filtro1 = driver.find_element(
#         By.XPATH, '//*[@id="result-paginated"]/div/div'
#     ).click()
#     sleep(2)
#     # driver.get_screenshot_as_file('/home/me/stocks/files/statusinvest_br/see.png')
#     button_filtro2 = driver.find_element(
#         By.XPATH, "/html/body/main/div[4]/div/div[3]/div/div/ul/li[3]"
#     ).click()
#     sleep(3)
#     # driver.find_element(By.CLASS_NAME,'btn-close').click()
#     # driver.get_screenshot_as_file('/home/me/stocks/files/statusinvest_br/see.png')
#     downld = driver.find_element(
#         By.XPATH, '//*[@id="main-2"]/div[4]/div/div[1]/div[2]/a'
#     ).click()
#     sleep(3)
#     # driver.close()
#
# fls = glob.glob("/home/me/stocks/files/statusinvest_br/*.*")
#
# for f in fls:
#     os.rename(f, f.replace(".crdownload", ""))
#
# b3 = pd.read_csv(
#     "/home/me/stocks/files/statusinvest_br/statusinvest-busca-avancada.csv", sep=";"
# )
# b3.tail()
#
# # %% [markdown]
# # ### Cotações do mercado americano
#
# # %%
#
#
# # %% [markdown]
# # ### usando spark
#
# # %%
# from pyspark.sql import SparkSession
#
# spark = SparkSession.builder.appName("B3 dataset").getOrCreate()
#
# b3_raw = spark.read.csv(
#     "/home/me/Downloads/statusinvest-busca-avancada.csv",
#     sep=";",
#     inferSchema=True,
#     header=True,
# )
#
# df = b3_raw.toPandas()
#
# spark.stop()
#
# df.head()
#
