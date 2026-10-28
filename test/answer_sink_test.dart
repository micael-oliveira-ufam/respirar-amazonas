import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:respirar_amazonas/services/answer_sink.dart';
import 'package:respirar_amazonas/services/api_client.dart';

Map<String, dynamic> _payload([String id = 'a3c1f2e4-0000-4000-8000-000000000001']) => {
      'submission_id': id,
      'nivel': 'low',
      'pontos': 1,
    };

FirestoreAnswerSink _sink(Future<void> Function(String, Map<String, dynamic>) writer, {Duration? timeout}) =>
    FirestoreAnswerSink(writer: writer, available: () => true, timeout: timeout ?? const Duration(seconds: 1));

void main() {
  group('FirestoreAnswerSink', () {
    test('grava em respostas/{submission_id} com o conteúdo do envio', () async {
      String? gotId;
      Map<String, dynamic>? gotData;
      await _sink((id, data) async {
        gotId = id;
        gotData = data;
      }).submit(_payload());
      expect(gotId, 'a3c1f2e4-0000-4000-8000-000000000001');
      expect(gotData!['nivel'], 'low');
    });

    test('não está configurado quando o Firebase não iniciou (modo local)', () {
      expect(FirestoreAnswerSink(available: () => false).isConfigured, isFalse);
      expect(FirebaseBootstrap.ready, isFalse); // nos testes o Firebase nunca é iniciado
    });

    test('recusa definitiva: permission-denied, invalid-argument, already-exists', () async {
      for (final code in ['permission-denied', 'invalid-argument', 'already-exists']) {
        final sink = _sink((_, __) async => throw FirebaseException(plugin: 'cloud_firestore', code: code));
        await expectLater(
          sink.submit(_payload()),
          throwsA(isA<ApiException>().having((e) => e.permanent, 'permanent', isTrue)),
          reason: code,
        );
      }
    });

    test('falha de rede (unavailable, deadline-exceeded) NÃO é definitiva: o item fica na fila', () async {
      for (final code in ['unavailable', 'deadline-exceeded', 'resource-exhausted']) {
        final sink = _sink((_, __) async => throw FirebaseException(plugin: 'cloud_firestore', code: code));
        await expectLater(
          sink.submit(_payload()),
          throwsA(isA<ApiException>().having((e) => e.permanent, 'permanent', isFalse)),
          reason: code,
        );
      }
    });

    test('sem resposta dentro do prazo: erro temporário', () async {
      final sink = _sink((_, __) => Completer<void>().future, timeout: const Duration(milliseconds: 20));
      await expectLater(
        sink.submit(_payload()),
        throwsA(isA<ApiException>().having((e) => e.permanent, 'permanent', isFalse)),
      );
    });

    test('envio sem submission_id é recusado sem tocar no Firebase', () async {
      var chamou = false;
      final sink = _sink((_, __) async => chamou = true);
      await expectLater(
        sink.submit({'nivel': 'low'}),
        throwsA(isA<ApiException>().having((e) => e.permanent, 'permanent', isTrue)),
      );
      expect(chamou, isFalse);
    });
  });
}
