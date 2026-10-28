import 'dart:async';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_core/firebase_core.dart';

import 'api_client.dart' show ApiException;

/// Destino das respostas compartilhadas pela pessoa.
///
/// [submit] termina sem erro quando o destino confirmou o recebimento; senão lança
/// [ApiException] (`permanent: true` = o destino recusou o conteúdo e reenviar não adianta).
abstract class AnswerSink {
  /// `false` = o destino não está disponível neste aparelho (modo local: nada é enviado).
  bool get isConfigured;

  Future<void> submit(Map<String, dynamic> payload);
}

/// Inicialização do Firebase. Falha silenciosa de propósito: sem configuração (por exemplo no iOS,
/// onde o arquivo `GoogleService-Info.plist` não foi fornecido) o app segue em modo local.
class FirebaseBootstrap {
  FirebaseBootstrap._();

  static bool ready = false;

  static Future<void> init() async {
    try {
      await Firebase.initializeApp();
      // Sem cache em disco: uma gravação pendente não fica escondida no SDK entre aberturas do app;
      // a fila de reenvio é a do próprio app (AnswerSync), que respeita a decisão da pessoa.
      FirebaseFirestore.instance.settings = const Settings(persistenceEnabled: false);
      ready = true;
    } catch (_) {
      ready = false;
    }
  }
}

/// Grava cada resposta como UM documento novo em `respostas/{submission_id}` no Firestore.
///
/// O identificador do documento é o `submission_id` (UUID aleatório por envio): reenviar a mesma
/// resposta aponta para o mesmo documento. As regras do Firestore (`firebase/firestore.rules`)
/// só permitem CRIAR; um reenvio de algo já gravado volta como `permission-denied`, tratado aqui
/// como recusa definitiva (o item sai da fila, sem duplicar dado).
class FirestoreAnswerSink implements AnswerSink {
  FirestoreAnswerSink({
    Future<void> Function(String id, Map<String, dynamic> data)? writer,
    bool Function()? available,
    this.timeout = const Duration(seconds: 20),
  })  : _writer = writer ?? _firestoreWriter,
        _available = available ?? (() => FirebaseBootstrap.ready);

  final Future<void> Function(String id, Map<String, dynamic> data) _writer;
  final bool Function() _available;
  final Duration timeout;

  static const collection = 'respostas';

  /// Códigos do Firestore que significam "este conteúdo não será aceito, não adianta repetir".
  static const permanentCodes = {'permission-denied', 'invalid-argument', 'already-exists', 'failed-precondition'};

  static Future<void> _firestoreWriter(String id, Map<String, dynamic> data) =>
      FirebaseFirestore.instance.collection(collection).doc(id).set({
        ...data,
        // Hora do servidor do Firebase: `registrado_em` vem do relógio do aparelho e pode estar errado.
        'recebido_em': FieldValue.serverTimestamp(),
      });

  @override
  bool get isConfigured => _available();

  @override
  Future<void> submit(Map<String, dynamic> payload) async {
    final id = payload['submission_id'];
    if (id is! String || id.isEmpty) {
      throw const ApiException('Envio sem identificador.', permanent: true, detail: 'submission_id ausente');
    }
    try {
      await _writer(id, payload).timeout(timeout);
    } on FirebaseException catch (e) {
      throw ApiException(
        'O Firebase recusou o envio (${e.code}).',
        permanent: permanentCodes.contains(e.code),
        detail: 'FirebaseException ${e.plugin}/${e.code}',
      );
    } on TimeoutException {
      throw const ApiException('Sem resposta do Firebase agora.', detail: 'TimeoutException');
    } catch (e) {
      throw ApiException('Não foi possível falar com o Firebase agora.', detail: '${e.runtimeType}');
    }
  }
}
