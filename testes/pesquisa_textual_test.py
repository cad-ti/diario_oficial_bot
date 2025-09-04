import unittest

from baixar_diarios_enviar_clipping import localizar_termo

class TestTermoEncontrado(unittest.TestCase):
    def setUp(self):
        self.texto = (
            "Este é um teste para verificar a ocorrência da segurança da informação "
            "em situações de ataque cibernético ao setor público. "
            "Outro exemplo: políticas de segurança da informação "
            "são essenciais contra ataque cibernético ao setor público."
        )
        self.destaque = '<span class="highlight" style="background:#FFA;">{termo_original}</span>'

    def test_palavra_com_acentos(self):
        termo = "informação"
        termo_destacado = self.destaque.format(termo_original=termo)
        resultados = localizar_termo(self.texto, termo, contexto=10)
        
        self.assertTrue(any("informação" in r for r in resultados))
        self.assertTrue(any(termo_destacado in r and termo_destacado in r for r in resultados))
        
    def test_palavra_sem_acentos(self):
        termo = "informacao"
        termo_destacado = self.destaque.format(termo_original="informação")
        resultados = localizar_termo(self.texto, termo, contexto=10)
        
        self.assertTrue(any(termo_destacado in r and termo_destacado in r for r in resultados))
        
    def test_palavra_caixa_alta(self):
        termo = "ATAQUE"
        termo_destacado = self.destaque.format(termo_original="ataque")
        resultados = localizar_termo(self.texto, termo, contexto=10)
        
        self.assertTrue(any(termo_destacado in r and termo_destacado in r for r in resultados))
        
    def test_palavra_em_ponto_final(self):
        termo = "público"
        termo_destacado = self.destaque.format(termo_original="público.")
        resultados = localizar_termo(self.texto, termo, contexto=10)
        
        self.assertTrue(any(termo_destacado in r and termo_destacado in r for r in resultados))
        
    def test_palavras_por_distacia_maxima(self):
        termo = "segurança+cibernetico~100"
        termo1_destacado = self.destaque.format(termo_original="segurança")
        termo2_destacado = self.destaque.format(termo_original="cibernético")
        resultados = localizar_termo(self.texto, termo, contexto=20)
        
        self.assertTrue(any(termo1_destacado in r and termo1_destacado in r for r in resultados))
        self.assertTrue(any(termo1_destacado in r and termo2_destacado in r for r in resultados))
        self.assertTrue(any(r.count("<span") >= 2 for r in resultados))
        
    def test_palavras_por_distacia_maxima_com_acento_e_caixa_alta(self):
        termo = "SEGURANÇA+CIBERNÉTICO~100"
        termo1_destacado = self.destaque.format(termo_original="segurança")
        termo2_destacado = self.destaque.format(termo_original="cibernético")
        resultados = localizar_termo(self.texto, termo, contexto=20)
        
        self.assertTrue(any(termo1_destacado in r and termo1_destacado in r for r in resultados))
        self.assertTrue(any(termo1_destacado in r and termo2_destacado in r for r in resultados))
        self.assertTrue(any(r.count("<span") >= 2 for r in resultados))
    
    def test_frase_com_acentos(self):
        termo = "segurança da informação"
        termo_destacado = self.destaque.format(termo_original=termo)
        resultados = localizar_termo(self.texto, termo, contexto=10)
        
        self.assertTrue(any(termo_destacado in r and termo_destacado in r for r in resultados))
        
    def test_frase_sem_acentos_com_espaco_no_fim(self):
        termo = "seguranca da informacao     "
        termo_destacado = self.destaque.format(termo_original="segurança da informação")
        resultados = localizar_termo(self.texto, termo, contexto=10)
        
        self.assertTrue(any(termo_destacado in r and termo_destacado in r for r in resultados))
        
    def test_frase_por_distacia_maxima_com_e_sem_acento_caixa_alta_e_baixa(self):
        termo = "SEGURANCA DA informação+ataque CIBERNÉTICO~100"
        resultados = localizar_termo(self.texto, termo, contexto=20)
        termo1_destacado = self.destaque.format(termo_original="segurança da informação")
        termo2_destacado = self.destaque.format(termo_original="ataque cibernético")
        
        self.assertTrue(any(termo1_destacado in r and termo1_destacado in r for r in resultados))
        self.assertTrue(any(termo1_destacado in r and termo2_destacado in r for r in resultados))
        self.assertTrue(any(r.count("<span") >= 2 for r in resultados))

    def test_frase_por_distacia_maxima_em_ponto_final(self):
        termo = "Segurança da Informação+Setor PúBlIcO~100"
        termo1_destacado = self.destaque.format(termo_original="segurança da informação")
        termo2_destacado = self.destaque.format(termo_original="setor público.")
        resultados = localizar_termo(self.texto, termo, contexto=20)
        
        self.assertTrue(any(termo1_destacado in r and termo1_destacado in r for r in resultados))
        self.assertTrue(any(termo1_destacado in r and termo2_destacado in r for r in resultados))
        self.assertTrue(any(r.count("<span") >= 2 for r in resultados))


if __name__ == "__main__":
    unittest.main()
