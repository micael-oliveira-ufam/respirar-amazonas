/*
 * Configuração do Firebase para o FORMULÁRIO DO SITE (navegador).
 *
 * Se este valor for null, o formulário mostra "envio indisponível" e não grava nada.
 * Configurado em 25/11/2026 com o objeto do console (abaixo).
 *
 * Como preencher (uma vez, pelo console do Firebase):
 *   1. Projeto "respirar-as" > Configurações do projeto > Seus apps > Adicionar app > Web (</>).
 *   2. Copie o objeto firebaseConfig que o console mostra e cole abaixo no lugar de null.
 *   3. Restrinja a chave: Google Cloud > APIs e serviços > Credenciais > a chave de API do
 *      navegador > "Restrições de aplicativo" > referenciadores HTTP com
 *      https://micael-oliveira-ufam.github.io/*
 *
 * Esses valores NÃO são segredos (o Firebase os publica em qualquer site que o use); a proteção
 * é a regra do Firestore (firebase/firestore.rules) e a restrição de domínio acima.
 */
// Objeto do console (app Web "Formulário do site", projeto respirar-as). Sem measurementId/Analytics:
// o formulário não usa Analytics, e coletar dados de navegação exigiria o termo de consentimento.
window.RESPIRAR_FIREBASE_WEB = {
  apiKey: "AIzaSyDOf9W8LjdLfOrwW-Qr6JMhfm3-u4X58Xc",
  authDomain: "respirar-as.firebaseapp.com",
  projectId: "respirar-as",
  storageBucket: "respirar-as.firebasestorage.app",
  messagingSenderId: "456508280412",
  appId: "1:456508280412:web:356fd9216f9635a0f16099"
};
