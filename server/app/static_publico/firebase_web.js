/*
 * Configuração do Firebase para o FORMULÁRIO DO SITE (navegador).
 *
 * Enquanto este valor for null, o formulário mostra "envio indisponível" e não grava nada.
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
window.RESPIRAR_FIREBASE_WEB = null;
// Exemplo do formato (NÃO é válido; substitua pelo objeto do seu console):
// window.RESPIRAR_FIREBASE_WEB = {
//   apiKey: "...", authDomain: "...", projectId: "...",
//   storageBucket: "...", messagingSenderId: "...", appId: "..."
// };
