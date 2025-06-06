from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Property, Thermostat, CalendarEvent, ThermostatCommand, UsageStatistics
from .serializers import (
    PropertySerializer, 
    ThermostatSerializer, 
    CalendarEventSerializer,
    ThermostatCommandSerializer, 
    UsageStatisticsSerializer
)
from .thermostat_adapters import get_thermostat_adapter

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own properties
        return Property.objects.filter(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def thermostats(self, request, pk=None):
        property = self.get_object()
        thermostats = Thermostat.objects.filter(property=property)
        serializer = ThermostatSerializer(thermostats, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def calendar(self, request, pk=None):
        property = self.get_object()
        
        if request.method == 'GET':
            events = CalendarEvent.objects.filter(property=property)
            serializer = CalendarEventSerializer(events, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = CalendarEventSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(property=property)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        property = self.get_object()
        period = request.query_params.get('period', 'month')
        
        # Logic to filter statistics based on period
        if period == 'week':
            # Last 7 days
            pass
        elif period == 'month':
            # Current month
            pass
        elif period == 'year':
            # Current year
            pass
        
        statistics = UsageStatistics.objects.filter(property=property)
        serializer = UsageStatisticsSerializer(statistics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def sync_calendar(self, request, pk=None):
        property = self.get_object()
        # Logic to sync with external calendar
        return Response({"status": "Calendar sync initiated"})


class ThermostatViewSet(viewsets.ModelViewSet):
    serializer_class = ThermostatSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see thermostats for their properties
        return Thermostat.objects.filter(property__owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        thermostat = self.get_object()
        
        # Use the appropriate adapter to get real-time status
        adapter = get_thermostat_adapter(thermostat)
        status_data = adapter.get_status()
        
        # Update the thermostat model with latest data
        thermostat.current_temperature = status_data.get('temperature')
        thermostat.current_humidity = status_data.get('humidity')
        thermostat.mode = status_data.get('mode', thermostat.mode)
        thermostat.is_online = status_data.get('online', True)
        thermostat.save(update_fields=['current_temperature', 'current_humidity', 'mode', 'is_online'])
        
        return Response(status_data)
    
    @action(detail=True, methods=['post'])
    def command(self, request, pk=None):
        thermostat = self.get_object()
        
        # Create a command record
        command_serializer = ThermostatCommandSerializer(data={
            'thermostat': thermostat.id,
            'command_type': request.data.get('command_type'),
            'parameters': request.data
        })
        
        if command_serializer.is_valid():
            command = command_serializer.save()
            
            # Use the appropriate adapter to send the command
            adapter = get_thermostat_adapter(thermostat)
            
            try:
                if command.command_type == 'set_temperature':
                    result = adapter.set_temperature(request.data.get('temperature'))
                elif command.command_type == 'set_mode':
                    result = adapter.set_mode(request.data.get('mode'))
                else:
                    result = adapter.send_command(command.command_type, command.parameters)
                
                # Update command status
                command.status = 'success'
                command.result = result
                command.save()
                
                # Update thermostat state if needed
                if command.command_type == 'set_temperature':
                    thermostat.target_temperature = request.data.get('temperature')
                    thermostat.save(update_fields=['target_temperature'])
                elif command.command_type == 'set_mode':
                    thermostat.mode = request.data.get('mode')
                    thermostat.save(update_fields=['mode'])
                
                return Response(result)
            
            except Exception as e:
                # Update command status to failed
                command.status = 'failed'
                command.result = {'error': str(e)}
                command.save()
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(command_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see calendar events for their properties
        return CalendarEvent.objects.filter(property__owner=self.request.user)


class UsageStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UsageStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see statistics for their properties
        return UsageStatistics.objects.filter(property__owner=self.request.user)
