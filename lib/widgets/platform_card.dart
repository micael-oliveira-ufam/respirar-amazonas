import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../theme/app_theme.dart';
import 'ui.dart';

/// Endereço do site público do projeto (GitHub Pages). Deve apontar para o mesmo site que `URL_PADRAO` de tool/gerar_pages.py (teste confere).
const kSitePublicoUrl = 'https://micael-oliveira-ufam.github.io/respirar-amazonas/';

/// Link da plataforma online (site público com os dados agregados), que o usuário abre no navegador.
class PlatformCard extends StatelessWidget {
  const PlatformCard({super.key});

  Future<void> _open(BuildContext context, String url) async {
    final ok = await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    if (!ok && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(behavior: SnackBarBehavior.floating, content: Text('Não foi possível abrir: $url')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    const url = kSitePublicoUrl;
    return AppCard(
      onTap: () => _open(context, url),
      child: Row(
        children: [
          const Icon(Icons.public_rounded, color: AppColors.brandDark, size: 30),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Plataforma online',
                    style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.ink)),
                const SizedBox(height: 4),
                const Text(
                  'Sintomas mais relatados, qualidade do ar, mapas e bairros de Manaus mais '
                  'afetados, em dados agregados e abertos a qualquer pessoa.',
                  style: TextStyle(height: 1.4, color: AppColors.muted),
                ),
                const SizedBox(height: 6),
                const Text(
                  url,
                  style: TextStyle(
                    color: Color(0xFF1565C0),
                    decoration: TextDecoration.underline,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
