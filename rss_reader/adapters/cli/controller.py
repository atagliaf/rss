# ✔ solo presentación
# ✔ ningún if de negocio


class CliController:
    def show(self, articles, summary: bool = False):
        for art in articles:
            print(f"{art.medio} [{art.titulo}")
            if summary and art.resumen:
                print(art.resumen)
                print("-" * 40)
