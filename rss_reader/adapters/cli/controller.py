# ✔ solo presentación
# ✔ ningún if de negocio


class CliController:
    def show(self, articles, summary: bool = False):
        for art in articles:
            print(f"{art.medio} [{art.titulo}")
            if summary and art.descripcion:
                print(art.descripcion)
                print("-" * 40)
