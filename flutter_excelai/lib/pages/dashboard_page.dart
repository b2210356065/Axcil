import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/business_provider.dart';
import '../providers/config_provider.dart';
import '../providers/history_provider.dart';
import '../utils/theme.dart';
import '../utils/constants.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final configAsync = ref.watch(configNotifierProvider);
    final businessAsync = ref.watch(businessNotifierProvider);
    final historyAsync = ref.watch(historyNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('ExcelAI Dashboard'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Welcome Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: AppTheme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.dashboard,
                            color: AppTheme.primary,
                          ),
                        ),
                        const SizedBox(width: 16),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Welcome to ExcelAI',
                                style: TextStyle(
                                  fontSize: 24,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                'AI-Powered Excel Generation System',
                                style: TextStyle(
                                  color: AppTheme.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Metrics Row
            Row(
              children: [
                Expanded(
                  child: _MetricCard(
                    title: 'Business Profiles',
                    value: businessAsync.when(
                      data: (profiles) => profiles.length.toString(),
                      loading: () => '...',
                      error: (_, __) => 'Error',
                    ),
                    icon: Icons.business,
                    color: AppTheme.primary,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _MetricCard(
                    title: 'Files Generated',
                    value: historyAsync.when(
                      data: (history) => history.length.toString(),
                      loading: () => '...',
                      error: (_, __) => 'Error',
                    ),
                    icon: Icons.insert_drive_file,
                    color: AppTheme.accent,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _MetricCard(
                    title: 'API Status',
                    value: configAsync.when(
                      data: (config) => config.isConfigured ? 'Active' : 'Setup Required',
                      loading: () => '...',
                      error: (_, __) => 'Error',
                    ),
                    icon: Icons.api,
                    color: AppTheme.secondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Quick Actions
            const Text(
              'Quick Actions',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 16,
              runSpacing: 16,
              children: ApiConstants.toolTypes.map((toolType) {
                return _ToolCard(
                  icon: ApiConstants.toolIcons[toolType]!,
                  name: ApiConstants.toolNames[toolType]!,
                  onTap: () {
                    // Navigate to tools page
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _MetricCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 12),
            Text(
              value,
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              title,
              style: const TextStyle(
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ToolCard extends StatelessWidget {
  final String icon;
  final String name;
  final VoidCallback onTap;

  const _ToolCard({
    required this.icon,
    required this.name,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 160,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.border),
        ),
        child: Column(
          children: [
            Text(
              icon,
              style: const TextStyle(fontSize: 32),
            ),
            const SizedBox(height: 8),
            Text(
              name,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
