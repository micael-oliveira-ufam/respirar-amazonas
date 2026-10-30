import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:respirar_amazonas/widgets/platform_card.dart';

void main() {
  testWidgets('Sobre mostra o endereço do site público, mesmo sem servidor configurado', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: PlatformCard())));
    expect(find.text('https://micael-oliveira-ufam.github.io/respirar-amazonas/'), findsOneWidget);
    expect(find.textContaining('ainda não disponível'), findsNothing);
  });
}
