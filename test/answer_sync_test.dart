import 'package:flutter_test/flutter_test.dart';
import 'package:respirar_amazonas/services/answer_sink.dart';
import 'package:respirar_amazonas/services/answer_sync.dart';
import 'package:respirar_amazonas/services/api_client.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeSink implements AnswerSink {
  _FakeSink({this.configured = true});

  final bool configured;
  final List<String> delivered = [];

  /// submission_id -> erro a lançar (consumido uma vez por tentativa).
  final Map<String, ApiException> failures = {};
  bool offline = false;

  @override
  bool get isConfigured => configured;

  @override
  Future<void> submit(Map<String, dynamic> payload) async {
    final id = payload['submission_id'] as String;
    if (offline) throw const ApiException('sem rede');
    final f = failures[id];
    if (f != null) throw f;
    delivered.add(id);
  }
}

Map<String, dynamic> _p(String id) => {'submission_id': id, 'nivel': 'low'};

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('sem destino configurado nada é enviado nem guardado', () async {
    final sync = AnswerSync(sink: _FakeSink(configured: false));
    expect(await sync.send(_p('a')), SyncResult.notConfigured);
    expect(await sync.pendingCount(), 0);
  });

  test('envio bem-sucedido', () async {
    final sink = _FakeSink();
    expect(await AnswerSync(sink: sink).send(_p('a')), SyncResult.sent);
    expect(sink.delivered, ['a']);
  });

  test('sem rede: vai para a fila e o próximo envio entrega a fila primeiro', () async {
    final sink = _FakeSink()..offline = true;
    final sync = AnswerSync(sink: sink);
    expect(await sync.send(_p('a')), SyncResult.queued);
    expect(await sync.pendingCount(), 1);
    sink.offline = false;
    expect(await sync.send(_p('b')), SyncResult.sent);
    expect(sink.delivered, ['a', 'b']);
    expect(await sync.pendingCount(), 0);
  });

  test('recusa definitiva: não entra na fila', () async {
    final sink = _FakeSink()..failures['a'] = const ApiException('negado', permanent: true);
    final sync = AnswerSync(sink: sink);
    expect(await sync.send(_p('a')), SyncResult.rejected);
    expect(await sync.pendingCount(), 0);
  });

  test('flush descarta o item recusado em definitivo e entrega os demais', () async {
    final sink = _FakeSink()..offline = true;
    final sync = AnswerSync(sink: sink);
    await sync.send(_p('a'));
    await sync.send(_p('b'));
    await sync.send(_p('c'));
    sink.offline = false;
    sink.failures['b'] = const ApiException('negado', permanent: true);
    expect(await sync.flush(), 2);
    expect(sink.delivered, ['a', 'c']);
    expect(await sync.pendingCount(), 0);
  });

  test('flush para na primeira falha de rede e mantém o resto na fila', () async {
    final sink = _FakeSink()..offline = true;
    final sync = AnswerSync(sink: sink);
    await sync.send(_p('a'));
    await sync.send(_p('b'));
    expect(await sync.flush(), 0);
    expect(await sync.pendingCount(), 2);
  });
}
