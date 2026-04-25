import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/api_config.dart';
import '../providers/config_provider.dart';
import '../utils/theme.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  final _formKey = GlobalKey<FormState>();
  final _geminiController = TextEditingController();
  final _claudeController = TextEditingController();
  final _openaiController = TextEditingController();
  String _defaultModel = 'gemini';

  @override
  void dispose() {
    _geminiController.dispose();
    _claudeController.dispose();
    _openaiController.dispose();
    super.dispose();
  }

  void _loadConfig(ApiConfig config) {
    _geminiController.text = config.geminiApiKey ?? '';
    _claudeController.text = config.claudeApiKey ?? '';
    _openaiController.text = config.openaiApiKey ?? '';
    _defaultModel = config.defaultModel;
  }

  Future<void> _saveConfig() async {
    if (_formKey.currentState!.validate()) {
      final config = ApiConfig(
        geminiApiKey: _geminiController.text.isEmpty ? null : _geminiController.text,
        claudeApiKey: _claudeController.text.isEmpty ? null : _claudeController.text,
        openaiApiKey: _openaiController.text.isEmpty ? null : _openaiController.text,
        defaultModel: _defaultModel,
      );

      await ref.read(configNotifierProvider.notifier).updateConfig(config);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Configuration saved successfully')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final configAsync = ref.watch(configNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        actions: [
          TextButton.icon(
            onPressed: _saveConfig,
            icon: const Icon(Icons.save, color: Colors.white),
            label: const Text('Save', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: configAsync.when(
        data: (config) {
          _loadConfig(config);
          return _buildForm();
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('Error: $error')),
      ),
    );
  }

  Widget _buildForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'API Configuration',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Configure your AI provider API keys',
              style: TextStyle(color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 24),

            // Gemini API Key
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: AppTheme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.flash_on, color: AppTheme.primary),
                        ),
                        const SizedBox(width: 12),
                        const Text(
                          'Gemini API Key',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _geminiController,
                      decoration: const InputDecoration(
                        labelText: 'API Key',
                        hintText: 'AIzaSy...',
                      ),
                      obscureText: true,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Claude API Key
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: AppTheme.secondary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.psychology, color: AppTheme.secondary),
                        ),
                        const SizedBox(width: 12),
                        const Text(
                          'Claude API Key',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _claudeController,
                      decoration: const InputDecoration(
                        labelText: 'API Key',
                        hintText: 'sk-ant-...',
                      ),
                      obscureText: true,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // OpenAI API Key
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: AppTheme.accent.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.smart_toy, color: AppTheme.accent),
                        ),
                        const SizedBox(width: 12),
                        const Text(
                          'OpenAI API Key',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _openaiController,
                      decoration: const InputDecoration(
                        labelText: 'API Key',
                        hintText: 'sk-proj-...',
                      ),
                      obscureText: true,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Default Model
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Default Model',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      value: _defaultModel,
                      decoration: const InputDecoration(
                        labelText: 'Select Default Model',
                      ),
                      items: const [
                        DropdownMenuItem(value: 'gemini', child: Text('Gemini 2.5 Flash')),
                        DropdownMenuItem(value: 'claude', child: Text('Claude 4.5 Sonnet')),
                        DropdownMenuItem(value: 'openai', child: Text('GPT-5')),
                      ],
                      onChanged: (value) {
                        setState(() {
                          _defaultModel = value!;
                        });
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
