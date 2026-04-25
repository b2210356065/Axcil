import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'utils/theme.dart';
import 'pages/dashboard_page.dart';
import 'pages/tools_page.dart';
import 'pages/functions_page.dart';
import 'pages/settings_page.dart';
import 'pages/history_page.dart';

void main() {
  runApp(
    const ProviderScope(
      child: ExcelAIApp(),
    ),
  );
}

class ExcelAIApp extends StatelessWidget {
  const ExcelAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ExcelAI',
      theme: AppTheme.lightTheme,
      debugShowCheckedModeBanner: false,
      home: const MainNavigator(),
    );
  }
}

class MainNavigator extends StatefulWidget {
  const MainNavigator({super.key});

  @override
  State<MainNavigator> createState() => _MainNavigatorState();
}

class _MainNavigatorState extends State<MainNavigator> {
  int _selectedIndex = 0;

  final List<Widget> _pages = const [
    DashboardPage(),
    ToolsPage(),
    FunctionsPage(),
    HistoryPage(),
    SettingsPage(),
  ];

  final List<NavigationRailDestination> _destinations = const [
    NavigationRailDestination(
      icon: Icon(Icons.dashboard_outlined),
      selectedIcon: Icon(Icons.dashboard),
      label: Text('Dashboard'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.build_outlined),
      selectedIcon: Icon(Icons.build),
      label: Text('Tools'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.functions_outlined),
      selectedIcon: Icon(Icons.functions),
      label: Text('Functions'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.history_outlined),
      selectedIcon: Icon(Icons.history),
      label: Text('History'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.settings_outlined),
      selectedIcon: Icon(Icons.settings),
      label: Text('Settings'),
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _selectedIndex,
            onDestinationSelected: (index) {
              setState(() {
                _selectedIndex = index;
              });
            },
            extended: MediaQuery.of(context).size.width > 1200,
            backgroundColor: AppTheme.surface,
            selectedIconTheme: const IconThemeData(color: AppTheme.primary),
            selectedLabelTextStyle: const TextStyle(color: AppTheme.primary),
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Column(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: AppTheme.primary,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.table_chart,
                      color: Colors.white,
                      size: 32,
                    ),
                  ),
                  if (MediaQuery.of(context).size.width > 1200) ...[
                    const SizedBox(height: 8),
                    const Text(
                      'ExcelAI',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            destinations: _destinations,
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(
            child: _pages[_selectedIndex],
          ),
        ],
      ),
    );
  }
}
